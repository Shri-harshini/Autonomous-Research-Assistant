import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import json
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse
import hashlib
import sqlite3
from pathlib import Path
import aiofiles
from .base_agent import BaseAgent, AgentMessage

@dataclass
class Source:
    """Data class to represent a source."""
    id: str
    url: str
    title: str
    content: str
    domain: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    credibility_score: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self.generate_id()
    
    def generate_id(self) -> str:
        """Generate unique ID for the source."""
        content_hash = hashlib.md5(f"{self.url}{self.title}{self.content[:100]}".encode()).hexdigest()
        return content_hash[:16]

@dataclass
class SourceCollection:
    """Data class to represent a collection of sources."""
    id: str
    name: str
    description: str
    sources: List[str] = field(default_factory=list)  # List of source IDs
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

class SourceManager(BaseAgent):
    """
    Source Manager responsible for:
    - Storing and retrieving sources
    - Tracking source metadata
    - Managing source collections
    - Deduplication and versioning
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the SourceManager with optional configuration."""
        super().__init__(
            name="SourceManager",
            description="Manages storage and retrieval of information sources"
        )
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Database configuration
        self.db_path = self.config.get("db_path", "data/sources.db")
        self.storage_dir = self.config.get("storage_dir", "data/sources")
        
        # Ensure directories exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db_connection = None
        self._initialize_database()
        
        # Cache for frequently accessed sources
        self.source_cache = {}
        self.cache_size_limit = self.config.get("cache_size_limit", 1000)
        
        # Deduplication settings
        self.duplicate_threshold = self.config.get("duplicate_threshold", 0.8)
    
    def _initialize_database(self):
        """Initialize the SQLite database."""
        try:
            self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.db_connection.row_factory = sqlite3.Row
            
            # Create tables
            self.db_connection.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    domain TEXT,
                    author TEXT,
                    publish_date TEXT,
                    last_accessed TEXT,
                    credibility_score REAL,
                    tags TEXT,  -- JSON array
                    metadata TEXT,  -- JSON object
                    content_hash TEXT,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db_connection.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    sources TEXT,  -- JSON array of source IDs
                    created_date TEXT,
                    last_updated TEXT,
                    metadata TEXT  -- JSON object
                )
            """)
            
            self.db_connection.execute("""
                CREATE TABLE IF NOT EXISTS source_relations (
                    source_id1 TEXT,
                    source_id2 TEXT,
                    relation_type TEXT,
                    confidence REAL,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (source_id1, source_id2, relation_type)
                )
            """)
            
            # Create indexes for better performance
            self.db_connection.execute("CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url)")
            self.db_connection.execute("CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain)")
            self.db_connection.execute("CREATE INDEX IF NOT EXISTS idx_sources_content_hash ON sources(content_hash)")
            
            self.db_connection.commit()
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process source management requests.
        
        Args:
            message: AgentMessage containing source management command
            
        Returns:
            AgentMessage with operation results
        """
        try:
            content = message.content_dict
            command = content.get("command", "")
            
            if command == "add_sources":
                return await self.add_sources(content.get("sources", []))
            
            elif command == "get_source":
                return await self.get_source(content.get("source_id"))
            
            elif command == "search_sources":
                return await self.search_sources(content.get("query", {}))
            
            elif command == "create_collection":
                return await self.create_collection(content.get("collection", {}))
            
            elif command == "get_collection":
                return await self.get_collection(content.get("collection_id"))
            
            elif command == "update_source":
                return await self.update_source(content.get("source_id"), content.get("updates", {}))
            
            elif command == "delete_source":
                return await self.delete_source(content.get("source_id"))
            
            elif command == "find_duplicates":
                return await self.find_duplicates(content.get("sources", []))
            
            elif command == "get_statistics":
                return await self.get_statistics()
            
            else:
                raise ValueError(f"Unknown command: {command}")
            
        except Exception as e:
            self.logger.error(f"Error in SourceManager: {str(e)}", exc_info=True)
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def add_sources(self, sources_data: List[Dict[str, Any]]) -> AgentMessage:
        """
        Add multiple sources to the database.
        
        Args:
            sources_data: List of source dictionaries
            
        Returns:
            AgentMessage with add results
        """
        added_sources = []
        duplicates = []
        errors = []
        
        for source_data in sources_data:
            try:
                # Create Source object
                source = Source(
                    id=source_data.get("id", ""),
                    url=source_data.get("url", ""),
                    title=source_data.get("title", ""),
                    content=source_data.get("content", ""),
                    domain=self.extract_domain(source_data.get("url", "")),
                    author=source_data.get("author"),
                    publish_date=source_data.get("publish_date"),
                    credibility_score=source_data.get("credibility_score", 0.5),
                    tags=source_data.get("tags", []),
                    metadata=source_data.get("metadata", {})
                )
                
                # Check for duplicates
                if await self.is_duplicate(source):
                    duplicates.append(source.id)
                    continue
                
                # Add to database
                await self._save_source_to_db(source)
                added_sources.append(source.id)
                
                # Update cache
                self._update_cache(source)
                
            except Exception as e:
                errors.append(f"Error adding source {source_data.get('url', 'unknown')}: {str(e)}")
        
        return AgentMessage.create(
            role="assistant",
            content={
                "status": "success",
                "added": len(added_sources),
                "duplicates": len(duplicates),
                "errors": len(errors),
                "source_ids": added_sources,
                "duplicate_ids": duplicates,
                "error_messages": errors
            },
            metadata={
                "agent": self.name,
                "total_processed": len(sources_data)
            }
        )
    
    async def get_source(self, source_id: str) -> AgentMessage:
        """
        Retrieve a source by ID.
        
        Args:
            source_id: ID of the source to retrieve
            
        Returns:
            AgentMessage with source data
        """
        try:
            # Check cache first
            if source_id in self.source_cache:
                source = self.source_cache[source_id]
            else:
                source = await self._load_source_from_db(source_id)
                if source:
                    self._update_cache(source)
            
            if not source:
                return AgentMessage.create(
                    role="assistant",
                    content={
                        "status": "error",
                        "error": f"Source not found: {source_id}"
                    },
                    metadata={"agent": self.name}
                )
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "source": source.__dict__
                },
                metadata={"agent": self.name}
            )
            
        except Exception as e:
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def search_sources(self, query: Dict[str, Any]) -> AgentMessage:
        """
        Search for sources based on query parameters.
        
        Args:
            query: Search parameters
            
        Returns:
            AgentMessage with search results
        """
        try:
            # Build SQL query
            sql = "SELECT * FROM sources WHERE 1=1"
            params = []
            
            # URL filter
            if query.get("url"):
                sql += " AND url LIKE ?"
                params.append(f"%{query['url']}%")
            
            # Domain filter
            if query.get("domain"):
                sql += " AND domain = ?"
                params.append(query["domain"])
            
            # Title filter
            if query.get("title"):
                sql += " AND title LIKE ?"
                params.append(f"%{query['title']}%")
            
            # Content filter
            if query.get("content"):
                sql += " AND content LIKE ?"
                params.append(f"%{query['content']}%")
            
            # Tags filter
            if query.get("tags"):
                for tag in query["tags"]:
                    sql += " AND tags LIKE ?"
                    params.append(f"%{tag}%")
            
            # Credibility score filter
            if query.get("min_credibility"):
                sql += " AND credibility_score >= ?"
                params.append(query["min_credibility"])
            
            # Date range filter
            if query.get("date_from"):
                sql += " AND publish_date >= ?"
                params.append(query["date_from"])
            
            if query.get("date_to"):
                sql += " AND publish_date <= ?"
                params.append(query["date_to"])
            
            # Limit and offset
            limit = query.get("limit", 50)
            offset = query.get("offset", 0)
            sql += f" ORDER BY last_accessed DESC LIMIT {limit} OFFSET {offset}"
            
            # Execute query
            cursor = self.db_connection.execute(sql, params)
            rows = cursor.fetchall()
            
            # Convert to Source objects
            sources = []
            for row in rows:
                source = self._row_to_source(row)
                sources.append(source.__dict__)
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "sources": sources,
                    "count": len(sources),
                    "query": query
                },
                metadata={
                    "agent": self.name,
                    "total_found": len(sources)
                }
            )
            
        except Exception as e:
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def create_collection(self, collection_data: Dict[str, Any]) -> AgentMessage:
        """
        Create a new source collection.
        
        Args:
            collection_data: Collection data
            
        Returns:
            AgentMessage with creation results
        """
        try:
            collection = SourceCollection(
                id=collection_data.get("id", self.generate_collection_id()),
                name=collection_data.get("name", ""),
                description=collection_data.get("description", ""),
                sources=collection_data.get("sources", []),
                metadata=collection_data.get("metadata", {})
            )
            
            # Save to database
            self.db_connection.execute("""
                INSERT OR REPLACE INTO collections 
                (id, name, description, sources, created_date, last_updated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                collection.id,
                collection.name,
                collection.description,
                json.dumps(collection.sources),
                collection.created_date,
                collection.last_updated,
                json.dumps(collection.metadata)
            ))
            
            self.db_connection.commit()
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "collection": collection.__dict__
                },
                metadata={"agent": self.name}
            )
            
        except Exception as e:
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def get_collection(self, collection_id: str) -> AgentMessage:
        """
        Retrieve a collection by ID.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            AgentMessage with collection data
        """
        try:
            cursor = self.db_connection.execute(
                "SELECT * FROM collections WHERE id = ?",
                (collection_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return AgentMessage.create(
                    role="assistant",
                    content={
                        "status": "error",
                        "error": f"Collection not found: {collection_id}"
                    },
                    metadata={"agent": self.name}
                )
            
            collection = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "sources": json.loads(row["sources"]),
                "created_date": row["created_date"],
                "last_updated": row["last_updated"],
                "metadata": json.loads(row["metadata"])
            }
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "collection": collection
                },
                metadata={"agent": self.name}
            )
            
        except Exception as e:
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def update_source(self, source_id: str, updates: Dict[str, Any]) -> AgentMessage:
        """
        Update a source with new data.
        
        Args:
            source_id: ID of the source to update
            updates: Dictionary of updates
            
        Returns:
            AgentMessage with update results
        """
        try:
            # Build update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in ["title", "content", "author", "publish_date", "credibility_score"]:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
                elif field == "tags":
                    set_clauses.append("tags = ?")
                    params.append(json.dumps(value))
                elif field == "metadata":
                    set_clauses.append("metadata = ?")
                    params.append(json.dumps(value))
            
            if not set_clauses:
                return AgentMessage.create(
                    role="assistant",
                    content={
                        "status": "error",
                        "error": "No valid fields to update"
                    },
                    metadata={"agent": self.name}
                )
            
            # Add last_accessed update
            set_clauses.append("last_accessed = ?")
            params.append(datetime.now().isoformat())
            params.append(source_id)
            
            # Execute update
            sql = f"UPDATE sources SET {', '.join(set_clauses)} WHERE id = ?"
            cursor = self.db_connection.execute(sql, params)
            
            if cursor.rowcount == 0:
                return AgentMessage.create(
                    role="assistant",
                    content={
                        "status": "error",
                        "error": f"Source not found: {source_id}"
                    },
                    metadata={"agent": self.name}
                )
            
            self.db_connection.commit()
            
            # Update cache
            if source_id in self.source_cache:
                cached_source = self.source_cache[source_id]
                for field, value in updates.items():
                    if hasattr(cached_source, field):
                        setattr(cached_source, field, value)
                cached_source.last_accessed = datetime.now().isoformat()
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "updated_fields": list(updates.keys())
                },
                metadata={"agent": self.name}
            )
            
        except Exception as e:
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def delete_source(self, source_id: str) -> AgentMessage:
        """
        Delete a source from the database.
        
        Args:
            source_id: ID of the source to delete
            
        Returns:
            AgentMessage with deletion results
        """
        try:
            # Delete from database
            cursor = self.db_connection.execute(
                "DELETE FROM sources WHERE id = ?",
                (source_id,)
            )
            
            if cursor.rowcount == 0:
                return AgentMessage.create(
                    role="assistant",
                    content={
                        "status": "error",
                        "error": f"Source not found: {source_id}"
                    },
                    metadata={"agent": self.name}
                )
            
            # Delete from relations
            self.db_connection.execute(
                "DELETE FROM source_relations WHERE source_id1 = ? OR source_id2 = ?",
                (source_id, source_id)
            )
            
            self.db_connection.commit()
            
            # Remove from cache
            if source_id in self.source_cache:
                del self.source_cache[source_id]
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "deleted_source": source_id
                },
                metadata={"agent": self.name}
            )
            
        except Exception as e:
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def find_duplicates(self, sources: List[Dict[str, Any]]) -> AgentMessage:
        """
        Find duplicate sources among the provided list.
        
        Args:
            sources: List of sources to check for duplicates
            
        Returns:
            AgentMessage with duplicate analysis
        """
        try:
            duplicates = []
            unique_sources = []
            
            for source_data in sources:
                source = Source(
                    url=source_data.get("url", ""),
                    title=source_data.get("title", ""),
                    content=source_data.get("content", ""),
                    domain=self.extract_domain(source_data.get("url", ""))
                )
                
                # Check if duplicate exists
                if await self.is_duplicate(source):
                    duplicates.append({
                        "url": source.url,
                        "title": source.title,
                        "duplicate_of": await self.find_duplicate_match(source)
                    })
                else:
                    unique_sources.append(source_data)
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "duplicates": duplicates,
                    "unique_count": len(unique_sources),
                    "duplicate_count": len(duplicates)
                },
                metadata={
                    "agent": self.name,
                    "total_checked": len(sources)
                }
            )
            
        except Exception as e:
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def get_statistics(self) -> AgentMessage:
        """
        Get database statistics.
        
        Returns:
            AgentMessage with statistics
        """
        try:
            # Source statistics
            cursor = self.db_connection.execute("SELECT COUNT(*) FROM sources")
            total_sources = cursor.fetchone()[0]
            
            cursor = self.db_connection.execute("SELECT COUNT(DISTINCT domain) FROM sources")
            unique_domains = cursor.fetchone()[0]
            
            cursor = self.db_connection.execute("SELECT AVG(credibility_score) FROM sources")
            avg_credibility = cursor.fetchone()[0] or 0
            
            # Collection statistics
            cursor = self.db_connection.execute("SELECT COUNT(*) FROM collections")
            total_collections = cursor.fetchone()[0]
            
            # Recent activity
            cursor = self.db_connection.execute("""
                SELECT COUNT(*) FROM sources 
                WHERE last_accessed > datetime('now', '-7 days')
            """)
            recent_access = cursor.fetchone()[0]
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "statistics": {
                        "total_sources": total_sources,
                        "unique_domains": unique_domains,
                        "average_credibility": round(avg_credibility, 2),
                        "total_collections": total_collections,
                        "recently_accessed": recent_access,
                        "cache_size": len(self.source_cache)
                    }
                },
                metadata={"agent": self.name}
            )
            
        except Exception as e:
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    # Helper methods
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    async def is_duplicate(self, source: Source) -> bool:
        """Check if a source is a duplicate."""
        # Check by URL
        cursor = self.db_connection.execute(
            "SELECT id FROM sources WHERE url = ?",
            (source.url,)
        )
        if cursor.fetchone():
            return True
        
        # Check by content hash
        content_hash = hashlib.md5(source.content.encode()).hexdigest()
        cursor = self.db_connection.execute(
            "SELECT id FROM sources WHERE content_hash = ?",
            (content_hash,)
        )
        if cursor.fetchone():
            return True
        
        # Check by title similarity (simplified)
        cursor = self.db_connection.execute(
            "SELECT id, title FROM sources WHERE title LIKE ?",
            (f"%{source.title[:50]}%",)
        )
        rows = cursor.fetchall()
        for row in rows:
            similarity = self.calculate_similarity(source.title, row["title"])
            if similarity > self.duplicate_threshold:
                return True
        
        return False
    
    async def find_duplicate_match(self, source: Source) -> Optional[str]:
        """Find the ID of the duplicate source."""
        # Check by URL
        cursor = self.db_connection.execute(
            "SELECT id FROM sources WHERE url = ?",
            (source.url,)
        )
        row = cursor.fetchone()
        if row:
            return row["id"]
        
        # Check by content hash
        content_hash = hashlib.md5(source.content.encode()).hexdigest()
        cursor = self.db_connection.execute(
            "SELECT id FROM sources WHERE content_hash = ?",
            (content_hash,)
        )
        row = cursor.fetchone()
        if row:
            return row["id"]
        
        return None
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (simplified)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0
    
    def generate_collection_id(self) -> str:
        """Generate unique collection ID."""
        return f"collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]}"
    
    async def _save_source_to_db(self, source: Source):
        """Save source to database."""
        content_hash = hashlib.md5(source.content.encode()).hexdigest()
        
        self.db_connection.execute("""
            INSERT OR REPLACE INTO sources 
            (id, url, title, content, domain, author, publish_date, last_accessed, 
             credibility_score, tags, metadata, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source.id,
            source.url,
            source.title,
            source.content,
            source.domain,
            source.author,
            source.publish_date,
            source.last_accessed,
            source.credibility_score,
            json.dumps(source.tags),
            json.dumps(source.metadata),
            content_hash
        ))
        
        self.db_connection.commit()
    
    async def _load_source_from_db(self, source_id: str) -> Optional[Source]:
        """Load source from database."""
        cursor = self.db_connection.execute(
            "SELECT * FROM sources WHERE id = ?",
            (source_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return self._row_to_source(row)
        
        return None
    
    def _row_to_source(self, row) -> Source:
        """Convert database row to Source object."""
        return Source(
            id=row["id"],
            url=row["url"],
            title=row["title"],
            content=row["content"],
            domain=row["domain"],
            author=row["author"],
            publish_date=row["publish_date"],
            last_accessed=row["last_accessed"],
            credibility_score=row["credibility_score"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )
    
    def _update_cache(self, source: Source):
        """Update source cache."""
        if len(self.source_cache) >= self.cache_size_limit:
            # Remove oldest entry
            oldest_key = next(iter(self.source_cache))
            del self.source_cache[oldest_key]
        
        self.source_cache[source.id] = source

# Example usage
async def test_source_manager():
    """Test function for the SourceManager."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    manager = SourceManager({
        "db_path": "test_data/sources_test.db",
        "storage_dir": "test_data/sources"
    })
    
    try:
        print("\nTesting Source Manager...")
        print("=" * 60)
        
        # Test 1: Add sources
        print("\n1. Adding sources...")
        test_sources = [
            {
                "url": "https://example.com/article1",
                "title": "AI in Healthcare: Recent Advances",
                "content": "Artificial intelligence is revolutionizing healthcare with applications in diagnosis, treatment, and drug discovery.",
                "author": "Dr. John Doe",
                "credibility_score": 0.8,
                "tags": ["AI", "healthcare", "technology"]
            },
            {
                "url": "https://example.com/article2",
                "title": "Machine Learning in Medical Diagnosis",
                "content": "Machine learning algorithms are improving diagnostic accuracy in radiology and pathology.",
                "author": "Dr. Jane Smith",
                "credibility_score": 0.9,
                "tags": ["machine learning", "diagnosis", "medical"]
            }
        ]
        
        add_result = await manager.process(AgentMessage.create(
            role="user",
            content={
                "command": "add_sources",
                "sources": test_sources
            }
        ))
        
        add_content = add_result.content_dict
        print(f"   Added: {add_content.get('added', 0)} sources")
        print(f"   Duplicates: {add_content.get('duplicates', 0)}")
        
        # Test 2: Search sources
        print("\n2. Searching sources...")
        search_result = await manager.process(AgentMessage.create(
            role="user",
            content={
                "command": "search_sources",
                "query": {
                    "domain": "example.com",
                    "limit": 10
                }
            }
        ))
        
        search_content = search_result.content_dict
        sources_found = search_content.get("sources", [])
        print(f"   Found: {len(sources_found)} sources")
        for source in sources_found:
            print(f"   - {source.get('title', '')} (Credibility: {source.get('credibility_score', 0):.2f})")
        
        # Test 3: Create collection
        print("\n3. Creating collection...")
        collection_result = await manager.process(AgentMessage.create(
            role="user",
            content={
                "command": "create_collection",
                "collection": {
                    "name": "AI Healthcare Research",
                    "description": "Collection of sources about AI in healthcare",
                    "sources": add_content.get("source_ids", [])
                }
            }
        ))
        
        collection_content = collection_result.content_dict
        if collection_content.get("status") == "success":
            collection = collection_content.get("collection", {})
            print(f"   Created collection: {collection.get('name', '')}")
            print(f"   Sources in collection: {len(collection.get('sources', []))}")
        
        # Test 4: Get statistics
        print("\n4. Getting statistics...")
        stats_result = await manager.process(AgentMessage.create(
            role="user",
            content={
                "command": "get_statistics"
            }
        ))
        
        stats_content = stats_result.content_dict
        if stats_content.get("status") == "success":
            stats = stats_content.get("statistics", {})
            print(f"   Total sources: {stats.get('total_sources', 0)}")
            print(f"   Unique domains: {stats.get('unique_domains', 0)}")
            print(f"   Average credibility: {stats.get('average_credibility', 0):.2f}")
            print(f"   Total collections: {stats.get('total_collections', 0)}")
        
        print("\n" + "=" * 60)
        print("✅ Source Manager tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        # Cleanup
        if manager.db_connection:
            manager.db_connection.close()

if __name__ == "__main__":
    asyncio.run(test_source_manager())
