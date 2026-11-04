"""Public distribution starts with no identity and enrolls without old profiles."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent))
from test_speaker_enrollment import EnrollmentTests
import speaker_settings
import speaker_targets as targets
from speaker_follow_setup import configure, check
from speaker_permission import load_settings
from speaker_delete import preview, delete


class PublicEnrollmentTests(EnrollmentTests):
    def setUp(self):
        super().setUp()
        (self.core/'speaker-template.json').unlink()
        (self.core/'lib').mkdir()
        lib=self.core/'lib/libonnxruntime.so.1.17.3'
        lib.write_bytes(b'test library')
        self.assets.pop('speaker-template.json')
        self.assets['lib/libonnxruntime.so.1.17.3']=hashlib.sha256(lib.read_bytes()).hexdigest()
        (self.core/'live-assets.json').write_text(json.dumps(dict(schema=2,enrollment='local_only',sha256=self.assets)))

    def test_public_empty_start_has_no_target_or_permission(self):
        self.assertIsNone(speaker_settings.verify_assets(self.core, use_selected=False))
        self.assertEqual(targets.list_targets(self.root), {'active_target':None,'targets':[]})
        with self.assertRaisesRegex(ValueError,'NO_ACTIVE_TARGET'): speaker_settings.verify_assets(self.core)
        with self.assertRaisesRegex(ValueError,'NO_ACTIVE_TARGET'): check(self.root)
        self.assertIsNone(load_settings(self.root)['threshold'])

    def test_select_clear_old_permission_and_runtime_load_new_template(self):
        self.enroll('alice'); configure(self.root,.65)
        targets.select(self.root,'alice')
        self.assertEqual(speaker_settings.verify_assets(self.core)['target_id'],'alice')
        self.assertIsNone(load_settings(self.root)['threshold'])
        with self.assertRaisesRegex(ValueError,'NO_BUILTIN_TARGET'): targets.select(self.root,'P01')

    def test_two_people_coexist_and_switch(self):
        self.enroll('alice'); self.enroll('bob')
        targets.select(self.root,'alice'); targets.select(self.root,'bob')
        self.assertEqual({r['target_id'] for r in targets.list_targets(self.root)['targets']},{'alice','bob'})
        self.assertEqual(speaker_settings.verify_assets(self.core)['target_id'],'bob')

    def test_custom_profile_import(self):
        # Public recipients enroll locally; old private baselines are not rebound.
        self.enroll('alice'); targets.select(self.root,'alice')
        self.assertFalse((self.core/'speaker-template.json').exists())
        self.assertEqual(speaker_settings.verify_assets(self.core)['template'][1],1.)

    def test_public_delete_last_user_does_not_reactivate_anyone(self):
        self.enroll('alice'); targets.select(self.root,'alice'); configure(self.root,.65)
        info=preview(self.root,'alice')
        delete(self.root,'alice','alice',info['token'])
        self.assertEqual(targets.list_targets(self.root)['targets'],[])
        self.assertIsNone(load_settings(self.root)['threshold'])
        with self.assertRaisesRegex(ValueError,'NO_ACTIVE_TARGET'): speaker_settings.verify_assets(self.core)

    def test_public_library_corruption_rejected_before_capture(self):
        (self.core/'lib/libonnxruntime.so.1.17.3').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Live asset hash'): self.enroll('alice')
        self.record.assert_not_called()


if __name__=='__main__':unittest.main()
