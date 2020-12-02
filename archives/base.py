class BaseArchiveRecipe(object):
    name = None
    active = False
    initial_checkpoint = None
    source = None
    target = None

    def track_filter(self, track, source):
        return True
