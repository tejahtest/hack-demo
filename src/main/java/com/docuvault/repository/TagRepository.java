package com.docuvault.repository;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/** Stores document tags and the reverse index from tag to documents. */
public class TagRepository {

    private final Map<String, Set<String>> tagsByDocument = new ConcurrentHashMap<>();
    private final Map<String, Set<String>> documentsByTag = new ConcurrentHashMap<>();

    public void addTag(String documentId, String tag) {
        tagsByDocument.computeIfAbsent(documentId, k -> ConcurrentHashMap.newKeySet()).add(tag);
        documentsByTag.computeIfAbsent(tag, k -> ConcurrentHashMap.newKeySet()).add(documentId);
    }

    public void removeTag(String documentId, String tag) {
        Set<String> tags = tagsByDocument.get(documentId);
        if (tags != null) {
            tags.remove(tag);
        }
        Set<String> docs = documentsByTag.get(tag);
        if (docs != null) {
            docs.remove(documentId);
        }
    }

    public Set<String> findTags(String documentId) {
        return tagsByDocument.getOrDefault(documentId, Set.of());
    }

    public List<String> findDocumentsByTag(String tag) {
        Set<String> docs = documentsByTag.get(tag);
        return docs == null ? List.of() : List.copyOf(docs);
    }
}
