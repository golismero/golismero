# -*- coding: utf-8 -*-
"""
@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt or
          U{http://www.opensource.org/licenses/mit-license.php})
"""

import logging

############################################################################
############################################################################

def init_logging(stream=None):
    """
    Initialize logging to standard output.
    """
    logger = logging.getLogger("snakemq")
    logger.setLevel(logging.CRITICAL)
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
                    "%(asctime)s %(name)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
