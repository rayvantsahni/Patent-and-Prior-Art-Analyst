"""
Simple rate limiting for Streamlit apps.

This module provides lightweight rate limiting suitable for Streamlit Cloud (free tier).
It uses session state to track usage per user session.
"""

import streamlit as st


class SimpleRateLimiter:
    """
    A simple session-based rate limiter for Streamlit apps.

    Features:
    - Per-session query limits (resets on browser refresh)
    - No external dependencies (pure session state)
    - Transparent about limitations

    Best for: Preventing honest users from overusing the app
    Not suitable for: Blocking malicious actors (can be bypassed by refreshing browser)

    Note: This provides "soft" rate limiting. Users can refresh the browser to get
    a new session with a fresh query counter. For stronger protection, consider
    IP-based tracking (requires external database) or authentication.
    """

    def __init__(self, max_queries_per_session=5):
        """
        Initialize the rate limiter.

        Args:
            max_queries_per_session (int): Maximum queries allowed per session
        """
        self.max_queries = max_queries_per_session

        # Initialize session state if needed
        if 'query_count' not in st.session_state:
            st.session_state.query_count = 0

    def can_query(self):
        """
        Check if the user can make another query.

        Returns:
            bool: True if query is allowed, False if limit reached
        """
        return st.session_state.query_count < self.max_queries

    def increment(self):
        """
        Increment the query counter.
        Should be called after a successful query.
        """
        st.session_state.query_count += 1

    def get_remaining_queries(self):
        """
        Get the number of queries remaining in this session.

        Returns:
            int: Number of queries remaining
        """
        remaining = self.max_queries - st.session_state.query_count
        return max(0, remaining)

    def get_usage_message(self):
        """
        Get a friendly message about current usage status.

        Returns:
            str: Usage message for display
        """
        remaining = self.get_remaining_queries()

        if remaining > 0:
            return f"✅ You have **{remaining}** of **{self.max_queries}** queries remaining in this session."
        else:
            return f"❌ Session limit reached (**{self.max_queries}** queries used). Refresh the page to start a new session."

    def show_usage_indicator(self):
        """
        Display a visual usage indicator in the Streamlit app.
        Shows a progress bar and usage message.
        """
        remaining = self.get_remaining_queries()
        used = self.max_queries - remaining

        # Calculate progress (inverted - more queries used = more progress)
        progress = used / self.max_queries

        # Show progress bar with color coding
        if remaining > 2:
            st.progress(progress, text=self.get_usage_message())
        elif remaining > 0:
            st.warning(self.get_usage_message())
        else:
            st.error(self.get_usage_message())
