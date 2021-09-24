def query_by_id(cls, id):
    """Query database by Id"""
    return cls.query.get_or_404(id)