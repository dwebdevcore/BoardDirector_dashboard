from json import loads
from django.core.exceptions import ValidationError
from django.core.files.storage import DefaultStorage
from django.db.models.fields import TextField
from django.db.models.fields.files import ImageFieldFile
from django.template.defaultfilters import slugify
from imagekit.processors import Resize
import jsonfield
import os

from imagekit.specs import ImageSpec


class Crop(object):
    def __init__(self, x=None, y=None, width=None, height=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def process(self, img):
        return img.crop((self.x, self.y, self.x + self.width, self.y + self.height))


def upload_to(instance, filename, crop_name):
    """
    Default function to specify a location to save crops to.
    
    :param instance: The model instance this crop field belongs to.
    :param filename: The image's filename this crop field operates on.
    :param crop_name: The crop name used when :attr:`CropFieldDescriptor.crop` was 
        called.
    """
    filename, ext = os.path.splitext(os.path.split(filename)[-1])
    return os.path.join('crops', u'%s-%s%s' % (filename, crop_name, ext))


class CropFieldFile(ImageFieldFile):
    """
    :attr:`CropFieldFile` objects are attached to a model's crop descriptor for each 
    specified crop spec.
    """

    def __init__(self, crop_name, spec, *args, **kwargs):
        self.crop_name = crop_name
        self.spec = spec
        super(CropFieldFile, self).__init__(*args, **kwargs)

    def delete(self, save=True):
        """
        Overriding delete method to not reset the model instance with an empty 
        field. This would override all our other crops and the JSON metadata.
        
        .. note:: This method should not be called directly, rather use 
            :attr:`CropFieldDescriptor.delete`.
        
        :param save: When true, the instance is saved to the database after 
            the crop was deleted.
        """
        if hasattr(self, '_file'):
            self.close()
            del self.file

        self.storage.delete(self.name)

        if save:
            self.instance.save()

        self._commited = False


class CropFieldDescriptor(object):
    """
    Crop descriptors are created by :attr:`CropField` and allow for creating, 
    inspecting and deleting crops.  
    """

    def __init__(self, instance, field, data):
        self.instance = instance
        self.field = field
        self.image = getattr(instance, field.image_field)

        self._data = {}
        self.data = data

    def create(self, name, spec, resize=None, save=True):
        """
        Create a new crop with the provided spec. For example the following code
        creates a crop of the original image starting at the X/Y coordinates of 
        0/0 and having a width of 100 pixels and a height of 150 pixels::
                                                                        
            >>> image.crops.create('thumbnail', (0, 0, 100, 150))
        
        Also allows for resizing the crop once it's been done. Useful for scaling
        the crop down to the desired target size::
        
            >>> (x, y, width, height) = crop = 0, 0, 100, 150
            >>> scaled_w, scaled_h = scaled = width / 3 * 2, height / 3 * 2
            >>> image.crops.create('thumbnail', crop, resize = scaled)
        
        Note that you should keep the ratio of width to height when resizing or 
        you'll end up with warped images.
                                         
        :param name: Crop name. This must be unique and is also used to generate
            the filename.
        :param spec: 4-tuple containing ``(x, y, width, height)``
        :param resize: 2-tuple for resizing the crop containing ``(width, height)``
        :param save: Boolean, if specified the model is saved back to DB after the crop.
        """
        name = self.validate_name(name)

        (x, y, width, height) = spec
        spec = {name: dict(x=x, y=y, width=width, height=height)}

        processors = [Crop(**spec[name])]

        if resize is not None:
            processors.append(Resize(resize[0], resize[1]))

        filename = self.get_filename(name)

        spec[name]['filename'] = filename

        # If a crop exists already, delete it first
        if hasattr(self, name):
            self.delete(name, save=False)

        generator = ImageSpec(self.image)
        generator.processors = processors
        content = generator.generate()
        self.field.storage.save(filename, content)

        self.data = dict(self.data, **spec)

        if save:
            self.instance.save()

        return getattr(self, name)

    def delete(self, name, save=True):
        """
        Delete the named crop. If save is specified, the model instance is saved
        after the deletion.

        :param name: Crop name
        :param save: Boolean, whether to save the model instance or not after 
            deleting the file.
        """
        name = self.validate_name(name)
        crop = getattr(self, name)
        delattr(self, name)
        del self._data[name]
        crop.delete(save)

    def clear(self, save=True):
        """ 
        Deletes all crops on this field.
        
        :param save: Boolean, whether to save the model instance or not after 
            deleting the file.
        """
        for crop in self:
            self.delete(crop.crop_name, save=False)

        if save:
            self.instance.save()

    def validate_name(self, name):
        """ 
        Makes sure that the crop name does not clash with any methods or 
        attributes on :attr:`CropFieldDescriptor`. 

        Raises :attr:`django.core.exceptions.ValidationError` in case there is 
        a clash.
        """

        if hasattr(self, name) and not isinstance(getattr(self, name), CropFieldFile):
            raise ValidationError(
                "Cannot override existing attribute '%s' with crop file." % name
            )
        return slugify(name).replace('-', '_')

    def get_filename(self, name):
        """
        Delegate filename creation to :attr:`field.upload_to`. 
        """
        return self.field.upload_to(self.instance, os.path.split(self.image.name)[-1], name)

    @property
    def data(self):
        """ 
        Return the raw picture data as a dictionary including path, coordinates, e.g.:
        
            >>> model.crops.data
            {
                'thumbnail': {
                    'x': 0, 'y': 0, 
                    'width': 100, 'height': 100,
                    'name': 'crops/image_thumbnail.png'
                }, 
                'skyscraper': {
                    'x': 0, 'y': 0,
                    'width': 100, height: 600,
                    'name': 'crops/image_skyscraper.png'
                }
            }
        
        """
        return self._data

    @data.setter
    def data(self, value):
        """
        Sets the data attribute and generates :attr:`CropFieldFiles`
        for convenience methods and attributes like :attr:`CropFieldFiles.delete`,
        :attr:`CropFieldFiles.url`, :attr:`CropFieldFiles.path`, etc.
        """
        if isinstance(value, basestring):
            try:
                value = loads(value)
            except ValueError:
                # print "%s.data: Unable to parse object from JSON" % self.__class__.__name__
                # print "Failed object: '%s'" % value
                return
        for name, spec in value.iteritems():
            name = self.validate_name(name)
            self._data[name] = spec

            if hasattr(self, name):
                continue

            setattr(self, name, CropFieldFile(
                name, spec,
                self.instance,
                self.field,
                spec['filename']))

    def __iter__(self):
        for key in self.data.keys():
            yield getattr(self, key)

    def __len__(self):
        return len(self.data.keys())


class CropFieldCreator(object):
    """ 
    Instead of using a metaclass for our custom field, we kind of
    follow :attr:`django.db.fields.files` in how to set up custom field 
    attributes on model objects. 
    """

    def __init__(self, field):
        self.field = field

    def __get__(self, instance, cls):
        if instance is None:
            return self.field
        return instance.__dict__[self.field.name]

    def __set__(self, instance, data):
        """ 
        Turn data from string into Python and store the CropFieldDescriptor
        on the instance 
        """
        instance.__dict__[self.field.name] = CropFieldDescriptor(instance, self.field,
                                                                 self.field.to_python(data))


class CropField(TextField):
    """
    Creates custom crops from a specified model field::
    
        class MyModel(models.Model):
            my_image = models.ImageField()
            my_crops = CropField('my_image')
                                            
    """

    def __init__(self, image_field=None, storage=DefaultStorage(),
                 upload_to=upload_to, editable=False, *args, **kwargs):
        """
        Custom field to generate crops of custom sizes in custom locations.
        
        :param image_field: The name of the image field this cropper operates on.
        :param storage: A custom storage backend to use.
        :param upload_to: A custom function to generate crop filenames. Must take
            three attributes, ``instance``, ``image`` and ``crop_name``. See
            :attr:`upload_to`.
        """
        assert image_field is not None, "You must specify an 'image_field' parameter."

        self.image_field = image_field

        self.storage = storage
        self.upload_to = upload_to

        kwargs['editable'] = editable

        self.json_field = jsonfield.JSONField(*args, **kwargs)

        kwargs['default'] = self.json_field.default

        super(CropField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(CropField, self).contribute_to_class(cls, name)
        setattr(cls, name, CropFieldCreator(self))

    def get_db_prep_value(self, value, **kwargs):
        # Some hacky support for migrations to work fine
        value = value.data if isinstance(value, CropFieldDescriptor) else value
        return self.json_field.get_db_prep_value(value, **kwargs)

    def to_python(self, value):
        return self.json_field.to_python(value)

    def deconstruct(self):
        name, path, args, kwargs = super(CropField, self).deconstruct()
        kwargs['image_field'] = self.image_field
        return name, path, args, kwargs


try:
    from south.modelsinspector import add_introspection_rules

    rules = [
        (
            (CropField,),
            [],  # Args
            {  # Kwargs
                "image_field": ["image_field", {}],
            }
        ),
    ]
    add_introspection_rules(rules, ["^croppy\.fields\.CropField"])
except ImportError:
    pass
