from encodings.base64_codec import base64_encode
from json import dumps

from django.contrib.contenttypes.models import ContentType

from committees.factories import CommitteeFactory
from common.api.exception_handler import WRONG_REQUEST
from common.utils import AccJsonRequestsTestCase
from dashboard.models import RecentActivity
from documents.models import Folder, Document, AuditTrail
from profiles.models import Membership


class DocumentsApiTests(AccJsonRequestsTestCase):
    def setUp(self):
        self.create_init_data()

    def test_document(self):
        self.login_admin()

        # Test create
        # ===========
        error = self.acc_post_json('api-documents-documents-list', {}, assert_status_code=400).json()
        self.assertEqual({
            "body": ["This field is required."],
            "name": ["This field is required."],
            'folder': ['This field is required.'],
            'detail': WRONG_REQUEST}, error)

        root = Folder.objects.get_account_root(self.account)

        storage_before = self.account.total_storage
        file_contents = 'File contents'
        document = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode(file_contents)[0],
            'name': 'The file.docx',
            'folder': root.id,
        }).json()

        self.assertEqual('The file.docx', document['name'])

        # Check that storage is updated
        self.account.refresh_from_db()
        self.assertEqual(len(file_contents), self.account.total_storage - storage_before)

        self.assertEqual(1, RecentActivity.objects.filter(account=self.account,
                                                          content_type=ContentType.objects.get_for_model(Document),
                                                          object_id=document['id'],
                                                          action_flag=RecentActivity.ADDITION).count())

        documents = self.acc_get('api-documents-documents-list').json()
        self.assertEqual(1, len(documents))
        self.assertEqual(document['id'], documents[0]['id'])

        document_content = self.acc_get('api-documents-documents-download', pk=document['id'])
        self.assertEqual(file_contents, document_content.content)

        # Update:
        # -----------
        updated_document = dict(document)
        updated_document['name'] = 'Updated.docx'
        updated_document['content'] = 'MUST BE IGNORED'
        self.acc_put_json('api-documents-documents-detail', pk=document['id'], json_data=updated_document)

        self.assertEqual(1, RecentActivity.objects.filter(account=self.account,
                                                          content_type=ContentType.objects.get_for_model(Document),
                                                          object_id=document['id'],
                                                          action_flag=RecentActivity.CHANGE).count())

        check_document = self.acc_get('api-documents-documents-detail', pk=document['id']).json()
        self.assertEqual('Updated.docx', check_document['name'])

        document_content = self.acc_get('api-documents-documents-download', pk=document['id'])
        self.assertEqual(file_contents, document_content.content)

        # Check move
        sub_folder = Folder.objects.create(parent=root, name='Test sub_folder', account=self.account)
        updated_document['folder'] = sub_folder.id
        self.acc_put_json('api-documents-documents-detail', pk=document['id'], json_data=updated_document)

        sub_folder.refresh_from_db()
        self.assertEqual(1, len(sub_folder.documents.all()))
        self.assertEqual('Updated.docx', sub_folder.documents.all()[0].name)

        # Delete it:
        # --------
        self.acc_delete('api-documents-documents-detail', pk=document['id'])
        self.acc_get('api-documents-documents-detail', pk=document['id'], assert_status_code=404)

        # BTW, no recent activity for deletions.. just puff.. and no document there (although old activity remains, but points nowhere)

    def test_create_large_document(self):
        self.login_admin()
        large_body = 1024 * 1024 * 25 * 'x'
        self.assertEqual(1024 * 1024 * 25, len(large_body))

        document = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode(large_body)[0],
            'name': 'The file.docx',
            'folder': Folder.objects.get_account_root(self.account).id,
        }).json()

        document = self.acc_get('api-documents-documents-download', pk=document['id'])
        self.assertEqual(large_body, document.content)

        # Same thing, but check plan failure
        self.account.plan.max_storage = 10000
        self.account.plan.save()

        self.account.refresh_from_db()
        storage_before = self.account.total_storage
        document = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode(large_body)[0],
            'name': 'The file.docx',
            'folder': Folder.objects.get_account_root(self.account).id,
        }, assert_status_code=400).json()

        self.assertEqual('Limit of data storage for your billing plan is exceeded, you can upgrade it in your profile!', document['message'])

        self.account.refresh_from_db()
        self.assertEqual(storage_before, self.account.total_storage)

    def test_folder(self):
        self.login_admin()

        folders = self.acc_get('api-documents-folders-list').json()
        initial_len = len(folders)

        root = Folder.objects.get_account_root(self.account)
        folder = self.acc_post_json('api-documents-folders-list', {
            'name': 'Test it!',
            'parent': root.id,
        }).json()

        self.assertEqual('Test it!', folder['name'])

        folders = self.acc_get('api-documents-folders-list').json()
        self.assertEqual(initial_len + 1, len(folders))

        # Duplicate error:
        error = self.acc_post_json('api-documents-folders-list', {
            'name': 'Test it!',
            'parent': root.id,
        }, assert_status_code=400).json()
        self.assertEqual({"non_field_errors": ["The fields parent, name must make a unique set."],
                          'detail': WRONG_REQUEST}, error)

        # Subfolder
        sub_folder = self.acc_post_json('api-documents-folders-list', {
            'name': "I'm a child",
            'parent': folder['id']
        }).json()

        folders = self.acc_get('api-documents-folders-list', data={'folder': folder['id']}).json()
        self.assertEqual(1, len(folders))
        self.assertEqual("I'm a child", folders[0]['name'])

        sub_folder['name'] = 'Changed!'
        self.acc_put_json('api-documents-folders-detail', pk=sub_folder['id'], json_data=sub_folder)

        folders = self.acc_get('api-documents-folders-list', data={'folder': folder['id']}).json()
        self.assertEqual(1, len(folders))
        self.assertEqual("Changed!", folders[0]['name'])

        # Check move
        target_folder = Folder.objects.create(parent=root, name="Target")
        sub_folder['parent'] = target_folder.id
        self.acc_put_json('api-documents-folders-detail', pk=sub_folder['id'], json_data=sub_folder)

        old_folder = Folder.objects.get(pk=folder['id'])
        self.assertEqual(0, len(old_folder.get_children()))

        target_folder.refresh_from_db()
        self.assertEqual(1, len(target_folder.get_children()))
        self.assertEqual("Changed!", target_folder.get_children()[0].name)

        self.acc_delete('api-documents-folders-detail', pk=sub_folder['id'])
        target_folder.refresh_from_db()
        self.assertEqual(0, len(target_folder.get_children()))
        self.acc_get('api-documents-folders-detail', pk=sub_folder['id'], assert_status_code=404)

    def test_access(self):
        # All previous tests used admin, which is kind of a god, i.e. can do anything. Let's test common member.
        self.login_member()
        root = Folder.objects.get_account_root(self.account)

        # User can't create folders in root
        self.acc_post_json('api-documents-folders-list', {
            'name': "The folder",
            'parent': root.id
        }, assert_status_code=403)

        # Nor documents
        self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode('File contents')[0],
            'name': 'The file.docx',
            'folder': root.id,
        }, assert_status_code=403)

        # He can, inside his own folder
        folder = self.acc_post_json('api-documents-folders-list', {
            'name': "The folder",
            'parent': self.membership.private_folder.id
        }).json()

        # And subfolder of it
        sub_folder = self.acc_post_json('api-documents-folders-list', {
            'name': "The subfolder",
            'parent': folder['id']
        }).json()

        # And files
        document = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode('File contents')[0],
            'name': 'The file.docx',
            'folder': self.membership.private_folder.id,
        }).json()

        # And move documents
        document['folder'] = sub_folder['id']
        self.acc_put_json('api-documents-documents-detail', pk=document['id'], json_data=document)

        # But not in other's folder:
        self.acc_post_json('api-documents-folders-list', {
            'name': "The folder",
            'parent': self.membership_admin.private_folder.id,
        }, assert_status_code=403)

        # Nor documents
        self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode('File contents')[0],
            'name': 'The file.docx',
            'folder': self.membership_admin.private_folder.id,
        }, assert_status_code=403)

        # And can't into committee he isn't in
        committee = CommitteeFactory(chairman=self.membership_admin)
        self.assertTrue(committee.folder)

        self.acc_post_json('api-documents-folders-list', {
            'name': "The folder",
            'parent': committee.folder.id,
        }, assert_status_code=403)

        # Nor documents
        self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode('File contents')[0],
            'name': 'The file.docx',
            'folder': committee.folder.id,
        }, assert_status_code=403)

        # But can as soon as he becomes a member
        committee.memberships.add(self.membership)
        self.acc_post_json('api-documents-folders-list', {
            'name': "The folder",
            'parent': committee.folder.id,
        })

        # Nor documents
        self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode('File contents')[0],
            'name': 'The file.docx',
            'folder': committee.folder.id,
        })

        # Other account must have no access to our documents, let's just check it
        self.init_second_account()
        self.login_admin2()

        self.acc_get('api-documents-documents-list', assert_status_code=403)
        self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode('File contents')[0],
            'name': 'The file.docx',
            'folder': root.id,
        }, assert_status_code=403)

    def test_lookup(self):
        self.login_admin()

        root = Folder.objects.get_account_root(self.account)
        sub_folder = Folder.objects.create(parent=root, account=self.account, name="sub_folder")
        sub_sub_folder = Folder.objects.create(parent=sub_folder, account=self.account, name="sub_sub_folder")
        document = Document.objects.create(folder=sub_folder, account=self.account, name="Super document", user=self.admin)

        # Arg is required
        self.acc_get('api-documents-folders-lookup', assert_status_code=400)

        lookup = self.acc_get('api-documents-folders-lookup', data={'init_for_document_id': document.id}).json()
        self.assertEqual(1, len(lookup))
        self.assertTrue(lookup[0]['state']['opened'])
        self.assertEqual(4, len(lookup[0]['children']))
        self.assertEqual('sub_folder', lookup[0]['children'][3]['text'])
        self.assertEqual(2, len(lookup[0]['children'][3]['children']))

        children = lookup[0]['children'][3]['children']
        self.assertFalse(children[0]['children'])
        self.assertFalse(children[1]['children'])
        self.assertIn('current', children[1]['text'])

        lookup = self.acc_get('api-documents-folders-lookup', data={'init_for_folder_id': sub_sub_folder.id}).json()
        self.assertEqual(1, len(lookup))
        self.assertTrue(lookup[0]['state']['opened'])
        self.assertEqual(4, len(lookup[0]['children']))
        self.assertEqual('sub_folder', lookup[0]['children'][3]['text'])
        self.assertEqual(1, len(lookup[0]['children'][3]['children']))

        lookup = self.acc_get('api-documents-folders-lookup', data={'folder_id': sub_folder.id}).json()
        self.assertEqual(1, len(lookup))
        self.assertEqual('sub_sub_folder', lookup[0]['text'])

    def test_share(self):
        root = Folder.objects.get_account_root(self.account)
        committee = CommitteeFactory(chairman=self.membership_admin)
        folder = Folder.objects.create(parent=committee.folder, account=self.account, name="sub_folder")

        self.login_member()
        self.acc_get('api-documents-folders-detail', pk=folder.id, assert_status_code=403)

        self.login_admin()
        self.acc_post_json('api-documents-folders-share', pk=folder.id, json_data={
            'memberships': [self.membership.id],
            'permission': 'view',
        })

        self.login_member()
        folder_json = self.acc_get('api-documents-folders-detail', pk=folder.id).json()
        self.assertEqual('sub_folder', folder_json['name'])

        # Should fail
        self.acc_delete('api-documents-folders-share', pk=folder.id, json_data={
            'id': folder_json['permissions'][0]['id']
        }, assert_status_code=403)

        # Drop permission: Should be no access again
        # -------------------------------------------
        self.login_admin()
        self.acc_delete('api-documents-folders-share', pk=folder.id, json_data={
            'permission_id': folder_json['permissions'][0]['id']
        })

        self.login_member()
        self.acc_get('api-documents-folders-detail', pk=folder.id, assert_status_code=403)

        # Try role permissions
        # --------------------
        self.login_admin()
        self.acc_post_json('api-documents-folders-share', pk=folder.id, json_data={
            'role': Membership.ROLES.member,
            'permission': 'edit',
        })

        self.login_member()
        folder_json = self.acc_get('api-documents-folders-detail', pk=folder.id).json()
        self.assertEqual('sub_folder', folder_json['name'])
        folder_json['name'] = 'Surprise!'

        self.acc_put_json('api-documents-folders-detail', pk=folder.id, json_data=folder_json)
        folder.refresh_from_db()
        self.assertEqual('Surprise!', folder.name)

        # Try wrong role permissions
        # --------------------------
        self.login_admin()
        folder_json = self.acc_get('api-documents-folders-detail', pk=folder.id).json()

        self.acc_delete('api-documents-folders-share', pk=folder.id, json_data={
            'permission_id': folder_json['permissions'][0]['id']
        })

        self.acc_post_json('api-documents-folders-share', pk=folder.id, json_data={
            'role': Membership.ROLES.guest,  # <------- NOTE: "guest"
            'permission': 'edit',
        })

        self.login_member()
        self.acc_get('api-documents-folders-detail', pk=folder.id, assert_status_code=403).json()

    def test_delete(self):
        self.login_admin()

        root = Folder.objects.get_account_root(self.account)

        file_contents = 'Hi there!'
        document = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode(file_contents)[0],
            'name': 'The file.docx',
            'folder': root.id,
        }).json()

        self.assertEqual(1, RecentActivity.objects.filter(account=self.account,
                                                          content_type=ContentType.objects.get_for_model(Document),
                                                          object_id=document['id'],
                                                          action_flag=RecentActivity.ADDITION).count())

        self.acc_delete('api-documents-documents-detail', pk=document['id'])

        # Recent activity is dropped
        self.assertEqual(0, RecentActivity.objects.filter(account=self.account,
                                                          content_type=ContentType.objects.get_for_model(Document),
                                                          object_id=document['id'],
                                                          action_flag=RecentActivity.ADDITION).count())

        revisions = list(AuditTrail.objects.filter(latest_version=document['id']))
        self.assertEqual(1, len(revisions))
        self.assertEqual(AuditTrail.DELETED, revisions[0].change_type)

    def test_update_file(self):
        """
        Demonstrates update sequence
        """
        self.login_admin()

        folder = self.membership_admin.private_folder

        # 1. Upload the file
        document = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode('Hi there!')[0],
            'name': 'The file.docx',
            'folder': folder.id,
        }).json()

        # 2. Upload replacement
        replaced = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode('Hi there! Replaced!')[0],
            'name': 'The file.docx',
            'folder': folder.id,
            'old_doc': document['id'],  # Provide 'old_doc'
        }).json()

        # 3. Delete original document, providing update change
        self.acc_delete('api-documents-documents-detail', pk=document['id'], json_data={'change_type': AuditTrail.UPDATED})  # AuditTrail.UPDATED == 0

        self.assertEqual(0, Document.objects.filter(pk=document['id']).count())
        self.assertEqual(1, Document.objects.filter(pk=replaced['id']).count())
        self.assertEqual(1, AuditTrail.objects.filter(latest_version=replaced['id']).count())

        # 4. Fetch replaced object again and get revisions list
        replaced = self.acc_get('api-documents-documents-detail', pk=replaced['id']).json()

        revisions = replaced['revisions']
        self.assertEqual(1, len(revisions))
        self.assertEqual(AuditTrail.UPDATED, revisions[0]['change_type'])
        self.assertEqual(self.admin.id, revisions[0]['user'])
        self.assertEqual(1, revisions[0]['revision'])

        # 5. Fetch revision contents: use new document id and revision
        old_body = self.acc_get('api-documents-documents-download-revision', pk=replaced['id'], revision=1).content
        self.assertEqual('Hi there!', old_body)

        documents = self.acc_get('api-documents-documents-list', data={'folder': self.membership_admin.private_folder.id}).json()
        self.assertEqual(1, len(documents))
        self.assertEqual(1, len(documents[0]['revisions']))

        # Check access is checked
        self.login_member()
        self.acc_get('api-documents-documents-download-revision', pk=replaced['id'], revision=1, assert_status_code=403)


