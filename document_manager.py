#!/usr/bin/env python3
"""
Document Manager
Handles document metadata and front matter
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import yaml


@dataclass
class DocumentMetadata:
    """Document front matter properties"""
    title: str = ""
    author: str = ""
    date: str = ""
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    layout: str = "default"
    draft: bool = False
    custom_fields: Dict[str, Any] = field(default_factory=dict)


class DocumentManager:
    """Manages document metadata and front matter"""
    
    def __init__(self):
        self.metadata = DocumentMetadata()
    
    def create_empty_metadata(self) -> DocumentMetadata:
        """Create empty metadata instance"""
        return DocumentMetadata()
    
    def parse_front_matter(self, text: str) -> Tuple[DocumentMetadata, str]:
        """Parse YAML front matter from markdown text"""
        if not text.startswith('---'):
            return self.metadata, text
        
        try:
            # Split front matter and content
            parts = text.split('---', 2)
            if len(parts) < 3:
                return self.metadata, text
            
            yaml_content = parts[1].strip()
            markdown_content = parts[2].lstrip('\n')
            
            # Parse YAML
            if yaml_content:
                yaml_data = yaml.safe_load(yaml_content)
                if yaml_data:
                    metadata = DocumentMetadata()
                    
                    # Update metadata with parsed data
                    for key, value in yaml_data.items():
                        if hasattr(metadata, key):
                            setattr(metadata, key, value)
                        else:
                            metadata.custom_fields[key] = value
                    
                    return metadata, markdown_content
            
            return self.metadata, markdown_content
            
        except yaml.YAMLError as e:
            print(f"YAML parsing error: {e}")
            return self.metadata, text
        except Exception as e:
            print(f"Front matter parsing error: {e}")
            return self.metadata, text
    
    def generate_front_matter(self, metadata: DocumentMetadata) -> str:
        """Generate YAML front matter from metadata"""
        # Check if we have any meaningful content
        has_content = any([
            metadata.title,
            metadata.author, 
            metadata.date,
            metadata.tags,
            metadata.categories,
            metadata.description,
            metadata.keywords,
            metadata.layout != "default",
            metadata.draft,
            metadata.custom_fields
        ])
        
        if not has_content:
            return ""
        
        yaml_data = {}
        
        # Add non-empty basic fields
        if metadata.title:
            yaml_data['title'] = metadata.title
        if metadata.author:
            yaml_data['author'] = metadata.author
        if metadata.date:
            yaml_data['date'] = metadata.date
        if metadata.description:
            yaml_data['description'] = metadata.description
        if metadata.tags:
            yaml_data['tags'] = metadata.tags
        if metadata.categories:
            yaml_data['categories'] = metadata.categories
        if metadata.keywords:
            yaml_data['keywords'] = metadata.keywords
        if metadata.layout != "default":
            yaml_data['layout'] = metadata.layout
        if metadata.draft:
            yaml_data['draft'] = metadata.draft
        
        # Add custom fields
        yaml_data.update(metadata.custom_fields)
        
        if not yaml_data:
            return ""
        
        try:
            yaml_output = yaml.dump(
                yaml_data, 
                default_flow_style=False, 
                sort_keys=False,
                allow_unicode=True
            )
            return f"---\n{yaml_output}---\n\n"
        except Exception as e:
            print(f"YAML generation error: {e}")
            return ""
    
    def extract_content_without_front_matter(self, text: str) -> str:
        """Extract markdown content without front matter"""
        if text.startswith('---'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                return parts[2].lstrip('\n')
        return text
    
    def update_front_matter(self, text: str, new_metadata: DocumentMetadata) -> str:
        """Update front matter in existing text"""
        # Extract content without front matter
        content = self.extract_content_without_front_matter(text)
        
        # Generate new front matter
        front_matter = self.generate_front_matter(new_metadata)
        
        # Combine
        return front_matter + content
    
    def validate_metadata(self, metadata: DocumentMetadata) -> List[str]:
        """Validate metadata and return list of issues"""
        issues = []
        
        # Validate date format if provided
        if metadata.date:
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', metadata.date):
                issues.append("Date should be in YYYY-MM-DD format")
        
        # Validate tags and categories (should be lists)
        if metadata.tags and not isinstance(metadata.tags, list):
            issues.append("Tags should be a list")
        
        if metadata.categories and not isinstance(metadata.categories, list):
            issues.append("Categories should be a list")
        
        return issues
    
    def get_metadata_summary(self, metadata: DocumentMetadata) -> str:
        """Get a human-readable summary of metadata"""
        summary_parts = []
        
        if metadata.title:
            summary_parts.append(f"Title: {metadata.title}")
        
        if metadata.author:
            summary_parts.append(f"Author: {metadata.author}")
        
        if metadata.date:
            summary_parts.append(f"Date: {metadata.date}")
        
        if metadata.tags:
            summary_parts.append(f"Tags: {', '.join(metadata.tags)}")
        
        if metadata.categories:
            summary_parts.append(f"Categories: {', '.join(metadata.categories)}")
        
        if metadata.draft:
            summary_parts.append("Status: Draft")
        
        if metadata.custom_fields:
            custom_count = len(metadata.custom_fields)
            summary_parts.append(f"Custom fields: {custom_count}")
        
        return "\n".join(summary_parts) if summary_parts else "No metadata"