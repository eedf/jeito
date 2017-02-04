from django.utils.deprecation import MiddlewareMixin
from cuser.middleware import CuserMiddleware as BaseCuserMiddleware


class CuserMiddleware(MiddlewareMixin, BaseCuserMiddleware):
    pass
