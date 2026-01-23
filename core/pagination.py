from rest_framework.pagination import PageNumberPagination,CursorPagination

class CustomLimitPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 50

class MyCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'