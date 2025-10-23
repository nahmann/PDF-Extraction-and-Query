"""
Prompts for AI document tagging.
"""

TAGGING_PROMPT = """
Analyze the following document and generate relevant tags and categories.

Document:
{document_text}

Available categories:
{categories}

Return tags in JSON format with category mappings.
"""

CATEGORY_MAPPING_PROMPT = """
Map this document to the most relevant categories.

Document summary:
{summary}

Categories:
{categories}

Return the top 3 most relevant categories with confidence scores.
"""
