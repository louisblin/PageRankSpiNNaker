import os
import sys
import tempfile
import unittest

import page_rank.model.tools.utils as utils


class TestSilenceOutput(unittest.TestCase):

    DATA_STDOUT = 'Hello, stdout World!'
    DATA_STDERR = 'Hello, stderr World!'

    def _assert_has_content(self, file_path, content):
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, 'r') as fd:
            self.assertEqual(fd.read(), content)

    def test_capture_stdout(self):
        file_path = tempfile.mktemp()

        with utils.silence_output(pipe_to=file_path):
            print(self.DATA_STDOUT),

        self._assert_has_content(file_path, self.DATA_STDOUT)

    def test_capture_stderr(self):
        file_path = tempfile.mktemp()

        with utils.silence_output(pipe_to=file_path):
            sys.stderr.write(self.DATA_STDERR)

        self._assert_has_content(file_path, self.DATA_STDERR)

    def test_capture_both(self):
        file_path = tempfile.mktemp()

        with utils.silence_output(pipe_to=file_path):
            print(self.DATA_STDOUT),
            sys.stderr.write(self.DATA_STDERR)

        self._assert_has_content(file_path, self.DATA_STDOUT + self.DATA_STDERR)

    def test_capture_both_disabled(self):
        file_path = tempfile.mktemp()

        with utils.silence_output(enable=False, pipe_to=file_path):
            print(self.DATA_STDOUT),
            sys.stderr.write(self.DATA_STDERR)

        self.assertFalse(os.path.exists(file_path))


class TestInstallRequirements(unittest.TestCase):

    # noinspection PyUnresolvedReferences
    def test_simple_install(self):
        file_path = tempfile.mktemp()
        with open(file_path, 'w') as fd:
            fd.write('tqdm==4.23.3\n')

        # Expect package to be missing
        with self.assertRaises(ImportError):
            import tqdm

        # Install package
        utils.install_requirements(requirements_file=file_path)

        # Should now work
        import tqdm
        self.assertEqual(tqdm.__version__, '4.23.3')


if __name__ == '__main__':
    unittest.main()