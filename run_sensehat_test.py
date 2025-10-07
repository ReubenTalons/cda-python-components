import sys
# Remove dist-packages from sys.path to prioritize venv packages
sys.path = [p for p in sys.path if 'dist-packages' not in p]
# Add it back at the end for GTK libraries only
sys.path.append('/usr/lib/python3/dist-packages')

# Now run the test
import unittest
loader = unittest.TestLoader()
suite = loader.loadTestsFromName('test_SenseHatEmulatorQuick')
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
