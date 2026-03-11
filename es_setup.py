from elasticsearch import Elasticsearch

# 엘라스틱 서버 연결 (9200 포트)
es = Elasticsearch("http://localhost:9200")

mapping = {
    "settings": {
        "analysis": {
            "analyzer": {
                "nori_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "store": {"type": "keyword"},
            "promotion_type": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "nori_analyzer"},
            "price": {"type": "integer"},
            "image_url": {"type": "keyword"}
        }
    }
}

# 인덱스 생성 (기존 있으면 무시)
es.indices.create(index="items", body=mapping, ignore=400)

print("✅ Elasticsearch index 'items' created with mapping")
