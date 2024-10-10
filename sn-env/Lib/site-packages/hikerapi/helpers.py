from typing import Dict, List, Optional


class HelperMixin:

    def media_likers(
        self,
        media_id: str,
        page_id: Optional[str] = None,
        count: Optional[int] = None,
        container: Optional[List[Dict]] = None,
        max_requests: Optional[int] = None,
    ) -> List[Dict]:
        """Get likers on media"""
        params = {"media_id": media_id, "end_cursor": page_id}
        return self._paging_request(
            "/gql/media/likers/chunk",
            params=params,
            count=count,
            container=container,
            page_key="end_cursor",
            max_requests=max_requests,
        )


class AsyncHelperMixin:

    async def media_likers(
        self,
        media_id: str,
        page_id: Optional[str] = None,
        count: Optional[int] = None,
        container: Optional[List[Dict]] = None,
        max_requests: Optional[int] = None,
    ) -> List[Dict]:
        """Get likers on media"""
        params = {"media_id": media_id, "end_cursor": page_id}
        return await self._paging_request(
            "/gql/media/likers/chunk",
            params=params,
            count=count,
            container=container,
            page_key="end_cursor",
            max_requests=max_requests,
        )
