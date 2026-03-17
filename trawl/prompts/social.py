SOCIAL_SEARCH_PROMPT = """
Generate highly optimized search engine queries specifically for social platforms.

You must generate:
1. A general social search query
2. An image search query
3. A video search query

Guidelines:
- Extract and prioritize the most important keywords from the user request
- Remove filler words and keep queries concise
- Add platform-specific operators like:
  - site:reddit.com for discussions and opinions
  - site:linkedin.com for professional insights
  - site:x.com for trending conversations
  - site:youtube.com for videos
- Combine multiple platforms when useful
- Tailor each query to maximize relevant results on social platforms

User request:
"""