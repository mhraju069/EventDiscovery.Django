from rest_framework.pagination import PageNumberPagination,CursorPagination

class CustomLimitPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 50

class MyCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'


def paginate_response(request, data, serializer_class, paginator_class, context=None):
    paginator = paginator_class()
    page = paginator.paginate_queryset(data, request)

    serializer = serializer_class(
        page,
        many=True,
        context=context or {"request": request}
    )

    return paginator.get_paginated_response(serializer.data)
