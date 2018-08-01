# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
import traceback
import unittest


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        loader = unittest.TestLoader()
        suite = loader.discover('tests')
        runner = unittest.TextTestRunner()
        runner.run(suite)
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
