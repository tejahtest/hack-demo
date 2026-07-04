package com.docuvault.api;

import com.docuvault.service.TagService;
import com.docuvault.util.VaultLogger;

import java.util.List;

/** Entry points for organising documents with tags. */
public class TagController {

    private final TagService tagService;

    public TagController(TagService tagService) {
        this.tagService = tagService;
    }

    /** A user tags a document so it can be grouped and found by label. */
    public void handleTagDocument(String documentId, String userId, String tag) {
        VaultLogger.logInfo("TagController", "Tag request: " + tag + " on " + documentId + " by " + userId);
        tagService.tagDocument(documentId, userId, tag);
    }

    /** A user removes a tag from a document. */
    public void handleUntagDocument(String documentId, String userId, String tag) {
        VaultLogger.logInfo("TagController", "Untag request: " + tag + " on " + documentId + " by " + userId);
        tagService.untagDocument(documentId, userId, tag);
    }

    /** A user lists every document they can view under a given tag. */
    public List<String> handleListDocumentsByTag(String userId, String tag) {
        VaultLogger.logInfo("TagController", "List-by-tag request: " + tag + " by " + userId);
        return tagService.listDocumentsByTag(userId, tag);
    }
}
