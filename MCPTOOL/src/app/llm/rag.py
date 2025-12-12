"""RAG (Retrieval Augmented Generation) 시스템"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from app.utils.config import settings
import os
import json


class TourismRAG:
    """여행지 정보 RAG 시스템"""
    
    def __init__(self):
        """ChromaDB 초기화"""
        os.makedirs(settings.chroma_persist_directory, exist_ok=True)
        
        # 임베딩 함수 설정
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        
        # ChromaDB 클라이언트 생성
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # 컬렉션 가져오기 또는 생성
        self.collection = self.client.get_or_create_collection(
            name="tourism_info",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_tourism_documents(self, items: List[Dict[str, Any]]):
        """여행지 정보를 벡터DB에 추가"""
        if not items:
            return
        
        ids = []
        documents = []
        metadatas = []
        
        for item in items:
            contentid = str(item.get("contentid", ""))
            if not contentid:
                continue
            
            # 문서 생성 (제목, 주소, 설명 등 결합)
            title = item.get("title", "")
            addr = item.get("addr1", "") or item.get("addr2", "")
            tel = item.get("tel", "")
            
            # 상세 설명이 있으면 포함 (추후 상세정보 API 호출 시 활용)
            doc_text = f"여행지명: {title}\n주소: {addr}\n전화번호: {tel}"
            
            ids.append(f"tourism_{contentid}")
            documents.append(doc_text)
            metadatas.append({
                "contentid": contentid,
                "title": title,
                "contenttypeid": str(item.get("contenttypeid", "")),
                "addr": addr,
            })
        
        if ids:
            # 기존 문서가 있으면 업데이트, 없으면 추가
            try:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception as e:
                print(f"문서 추가 중 오류: {str(e)}")
    
    def search_relevant_documents(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """쿼리와 관련된 문서 검색"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            documents = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0.0
                    
                    documents.append({
                        "document": doc,
                        "metadata": metadata,
                        "distance": distance
                    })
            
            return documents
        except Exception as e:
            print(f"문서 검색 중 오류: {str(e)}")
            return []
    
    def get_context_for_course(self, items: List[Dict[str, Any]], query: str) -> str:
        """코스 생성용 컨텍스트 생성"""
        # RAG로 관련 문서 검색
        relevant_docs = self.search_relevant_documents(query, n_results=3)
        
        # 검색된 문서 내용 추출
        context_parts = []
        for doc in relevant_docs:
            context_parts.append(doc["document"])
        
        # 검색된 아이템 정보 추가
        item_info = []
        for item in items[:5]:  # 상위 5개만
            title = item.get("title", "")
            addr = item.get("addr1", "") or item.get("addr2", "")
            item_info.append(f"- {title} ({addr})")
        
        if item_info:
            context_parts.append("\n검색된 여행지:\n" + "\n".join(item_info))
        
        return "\n\n".join(context_parts)


# 전역 RAG 인스턴스
_rag_instance: Optional[TourismRAG] = None


def get_rag() -> TourismRAG:
    """RAG 인스턴스 싱글톤 반환"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = TourismRAG()
    return _rag_instance

