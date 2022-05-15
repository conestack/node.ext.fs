from node.ext.fs.interfaces import IFileAddedEvent
from zope.interface import implementer
from zope.lifecycleevent import ObjectAddedEvent


@implementer(IFileAddedEvent)
class FileAddedEvent(ObjectAddedEvent):
    """Event which gets triggered when file is added to directory."""
