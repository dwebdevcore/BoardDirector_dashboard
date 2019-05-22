from encodings.base64_codec import base64_encode

from common.utils import AccJsonRequestsTestCase
from documents.models import Folder, Annotation
from profiles.models import Membership


class DocumentAnnotationsApiTests(AccJsonRequestsTestCase):
    def setUp(self):
        self.create_init_data()

    def test_annotations_crud(self):
        self.login_admin()

        root = Folder.objects.get_account_root(self.account)
        # Workaround permissions bug
        some_folder = Folder.objects.create(parent=root, name="Test folder", account=self.account)
        some_folder2 = Folder.objects.create(parent=some_folder, name="Test folder2", account=self.account)

        # Create some document to play with
        file_contents = 'File contents'
        document = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode(file_contents)[0],
            'name': 'The file.docx',
            'folder': some_folder2.id,
        }).json()

        annotations = self.acc_get('api-documents-annotations-list', data={'document_id': document['id']}).json()
        self.assertEqual([], annotations['annotations'])

        response = self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotations': [{
                'document_page': 3,
                'type': Annotation.TYPE_PEN,
                'geometry_tools_version': 42,
                'cargo_json': {
                    'Just any possible content': ['you may ever want']
                },
                'comments': [{
                    'text': 'Hey there!',
                }, {
                    'text': 'One more time!'
                }]
            }, {
                'document_page': 4,
                'local_id': 142,
                'type': Annotation.TYPE_STICKY_TAB,
                'geometry_tools_version': 42,
                'cargo_json': {
                    'lines': [1, 2, 3, 4]
                },
                'comments': [{
                    'text': 'Another annotation',
                }]
            }]
        }).json()

        ann1 = Annotation.objects.get(pk=response['annotations'][0]['id'])
        self.assertEqual(Annotation.TYPE_PEN, ann1.type)
        self.assertEqual(42, ann1.geometry_tools_version)
        self.assertEqual({'Just any possible content': ['you may ever want']}, ann1.cargo_json)
        self.assertEqual(3, ann1.document_page)
        self.assertEqual(self.admin, ann1.author_user)

        comments = list(ann1.comments.all())
        self.assertEqual(2, len(comments))
        self.assertEqual('One more time!', comments[1].text)
        self.assertEqual(self.admin, comments[1].author_user)

        ann2 = Annotation.objects.get(pk=response['annotations'][1]['id'])
        self.assertEqual('Another annotation', ann2.comments.get().text)

        annotations = self.acc_get('api-documents-annotations-list', data={'document_id': document['id']}).json()
        self.assertEqual(2, len(annotations['annotations']))
        self.assertEqual('142', annotations['annotations'][1]['local_id'])

        # Check page request
        annotations = self.acc_get('api-documents-annotations-list', data={'document_id': document['id'], 'from_page': 3, 'to_page': 3}).json()
        self.assertEqual(1, len(annotations['annotations']))
        self.assertEqual('Hey there!', annotations['annotations'][0]['comments'][0]['text'])

        # Check other user
        # -----------------

        # Check no access to annotations for document without access
        self.login_member()
        self.acc_get('api-documents-annotations-list', data={'document_id': document['id']}, assert_status_code=403).json()

        self.login_admin()
        # Share folder
        self.acc_post_json('api-documents-folders-share', pk=some_folder.id, json_data={
            'role': Membership.ROLES.member,
            'permission': 'view',
        })

        # Now do it legally
        self.login_member()
        annotations = self.acc_get('api-documents-annotations-list', data={'document_id': document['id']}).json()
        self.assertEqual(0, len(annotations['annotations']))

        self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotations': [{
                'document_page': 3,
                'type': Annotation.TYPE_PEN,
                'geometry_tools_version': 42,
                'cargo_json': {},
                'comments': [{
                    'text': 'Comment from other user yay!',
                }]
            }]})

        annotations = self.acc_get('api-documents-annotations-list', data={'document_id': document['id']}).json()
        self.assertEqual(1, len(annotations['annotations']))

        self.assertEqual(3, Annotation.objects.filter(document_id=document['id']).count())

        # Try update annotations of other user
        response = self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotations': [{
                'id': ann1.id,
                'document_page': 3,
                'type': Annotation.TYPE_PEN,
                'geometry_tools_version': 42,
                'cargo_json': {},
                'comments': [{
                    'text': 'New comment from the Hacker',
                }]
            }]}, assert_status_code=201).json()

        self.assertEqual(["Can't update annotation with id=1 which doesn't belong to current user or document."], response['notes'])

        self.login_admin()
        self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotations': [{
                'id': ann1.id,
                'document_page': 3,
                'type': Annotation.TYPE_PEN,
                'geometry_tools_version': 42,
                'cargo_json': {},
                'comments': [{
                    'text': 'New comment from the Admin',
                }]
            }]}).json()

        self.assertEqual(3, Annotation.objects.filter(document_id=document['id']).count())
        self.assertEqual(3, ann1.comments.count())
        self.assertEqual('New comment from the Admin', list(ann1.comments.all())[-1].text)

        # Check delete
        fake_annotation_id = ann1.id + 10000
        response = self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotation_id_to_delete': [ann1.id, fake_annotation_id],
        }).json()

        self.assertFalse(Annotation.objects.filter(pk=ann1.id).exists())
        self.assertEqual([ann1.id], response['annotation_id_to_delete'])  # will be echoed with successfully deleted annotations
        # skip not existing annotations
        self.assertEqual(["Can't delete annotation with id=%d as it doesn't belong to current user or document" % (fake_annotation_id,)], response['notes'])

    def test_shared_annotations(self):
        self.login_admin()

        root = Folder.objects.get_account_root(self.account)
        # Workaround permissions bug
        some_folder = Folder.objects.create(parent=root, name="Test folder", account=self.account)
        some_folder2 = Folder.objects.create(parent=some_folder, name="Test folder2", account=self.account)

        self.acc_post_json('api-documents-folders-share', pk=some_folder.id, json_data={
            'role': Membership.ROLES.member,
            'permission': 'view',
        })

        # Create some document to play with
        file_contents = 'File contents'
        document = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode(file_contents)[0],
            'name': 'The file.docx',
            'folder': some_folder2.id,
        }).json()

        annotations = self.acc_get('api-documents-annotations-list', data={'document_id': document['id']}).json()
        self.assertEqual([], annotations['annotations'])

        response = self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotations': [{
                'document_page': 3,
                'type': Annotation.TYPE_PEN,
                'geometry_tools_version': 42,
                'shared': True,
                'cargo_json': {
                    'Just any possible content': ['you may ever want']
                },
                'comments': [{
                    'text': 'This one is shared',
                }]
            }, {
                'document_page': 4,
                'local_id': 142,
                'type': Annotation.TYPE_STICKY_TAB,
                'geometry_tools_version': 42,
                'shared': False,
                'cargo_json': {
                    'lines': [1, 2, 3, 4]
                },
                'comments': [{
                    'text': 'And this one is private',
                }]
            }]
        }).json()

        # Check only shared is visible
        self.login_member()

        annotations_resp = self.acc_get('api-documents-annotations-list', data={'document_id': document['id']}).json()
        annotations = annotations_resp['annotations']
        self.assertEqual(1, len(annotations))
        a = annotations[0]
        self.assertEqual(response['annotations'][0]['id'], a['id'])
        self.assertTrue(a['shared'])

        # User can add comments, but not modify other's comments
        a['comments'][0]['text'] = 'Hey there, I\'m, a hacker!'

        response = self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotations': annotations
        }).json()
        self.assertEqual(["Can't update comment id=%d: it either not exists or belongs to other user" % a['comments'][0]['id']], response['notes'])

        annotations[0]['comments'] = [{'text': 'And here is mine'}]  # note: ignore other's comments on update
        self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotations': annotations
        }).json()

        annotations_resp = self.acc_get('api-documents-annotations-list', data={'document_id': document['id']}).json()
        annotations = annotations_resp['annotations']
        self.assertEqual(2, len(annotations[0]['comments']))
        self.assertEqual(self.admin.id, annotations[0]['comments'][0]['author_user_id'])
        self.assertEqual(self.user.id, annotations[0]['comments'][1]['author_user_id'])

        # !!!!!
        # Note corner-case: In case someone sends update for other's user comment,
        # subsequent update to his comment will fail because other's will raise exception
        annotations[0]['comments'][0]['text'] = 'Change it!'
        annotations[0]['comments'][1]['text'] = 'Change it!'
        self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotations': annotations
        }).json()

        annotations_resp = self.acc_get('api-documents-annotations-list', data={'document_id': document['id']}).json()
        comments = annotations_resp['annotations'][0]['comments']
        self.assertNotEqual('Change it!', comments[0]['text'])
        self.assertNotEqual('Change it!', comments[1]['text'])

        # Check delete:
        response = self.acc_post_json('api-documents-annotations-list', {
            'document_id': document['id'],
            'annotation_id_to_delete': [a['id']],
        }).json()

        self.assertEqual(["Can't delete annotation with id=%d as it doesn't belong to current user or document" % a['id']], response['notes'])
        self.assertTrue(Annotation.objects.filter(pk=a['id']).exists())
