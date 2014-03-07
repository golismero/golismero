# -*- coding: utf-8 -*-
"""
@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt or
          U{http://www.opensource.org/licenses/mit-license.php})
"""

class SnakeMQException(Exception):
    pass

###################################################################

class NoConnection(SnakeMQException):
    pass

###################################################################
# link
class SendNotFinished(SnakeMQException):
    pass

###################################################################
# messaging

class SnakeMQBrokenFormat(SnakeMQException):
    pass

class SnakeMQBrokenPacket(SnakeMQBrokenFormat):
    """
    Received packet has wrong structure.
    """
    pass

class SnakeMQBrokenMessage(SnakeMQBrokenFormat):
    """
    Received message has wrong structure.
    """
    pass

class SnakeMQIncompatibleProtocol(SnakeMQException):
    """
    Remote side has incompatible protocol version.
    """
    pass

class SnakeMQNoIdent(SnakeMQException):
    """
    Remote side did not identified itself.
    """
    pass

class SnakeMQUnknownRoute(SnakeMQException):
    """
    Message destination/route unknown.
    """
    pass
