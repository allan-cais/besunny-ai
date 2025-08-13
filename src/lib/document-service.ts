// Document Service
// Handles document-related operations and management

import { supabase } from './supabase';
import type { Document, DocumentType, Project } from '../types';
import { errorUtils, createError } from './error-handling';
import { config } from '../config';

// Document service class
export class DocumentService {
  // Get documents for a project
  async getProjectDocuments(projectId: string): Promise<Document[]> {
    try {
      const { data: documents, error } = await supabase
        .from('documents')
        .select('*')
        .eq('project_id', projectId)
        .order('created_at', { ascending: false });

      if (error) {
        throw createError.database(
          'Failed to fetch project documents',
          { action: 'get_project_documents', projectId }
        );
      }

      return documents || [];
    } catch (error) {
      throw createError.database(
        'Error fetching project documents',
        { action: 'get_project_documents', projectId },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Get documents by type
  async getDocumentsByType(type: DocumentType, projectId?: string): Promise<Document[]> {
    try {
      let query = supabase
        .from('documents')
        .select('*')
        .eq('type', type)
        .order('created_at', { ascending: false });

      if (projectId) {
        query = query.eq('project_id', projectId);
      }

      const { data: documents, error } = await query;

      if (error) {
        throw createError.database(
          'Failed to fetch documents by type',
          { action: 'get_documents_by_type', type, projectId }
        );
      }

      return documents || [];
    } catch (error) {
      throw createError.database(
        'Error fetching documents by type',
        { action: 'get_documents_by_type', type, projectId },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Get document by ID
  async getDocumentById(documentId: string): Promise<Document | null> {
    try {
      const { data: document, error } = await supabase
        .from('documents')
        .select('*')
        .eq('id', documentId)
        .single();

      if (error) {
        if (error.code === 'PGRST116') {
          return null; // Document not found
        }
        throw createError.database(
          'Failed to fetch document',
          { action: 'get_document_by_id', documentId }
        );
      }

      return document;
    } catch (error) {
      throw createError.database(
        'Error fetching document',
        { action: 'get_document_by_id', documentId },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Create new document
  async createDocument(document: Omit<Document, 'created_at' | 'updated_at'>): Promise<Document> {
    try {
      const { data: newDocument, error } = await supabase
        .from('documents')
        .insert(document)
        .select()
        .single();

      if (error) {
        throw createError.database(
          'Failed to create document',
          { action: 'create_document', documentId: document.id }
        );
      }

      return newDocument;
    } catch (error) {
      throw createError.database(
        'Error creating document',
        { action: 'create_document', documentId: document.id },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Update document
  async updateDocument(documentId: string, updates: Partial<Document>): Promise<Document> {
    try {
      const { data: updatedDocument, error } = await supabase
        .from('documents')
        .update(updates)
        .eq('id', documentId)
        .select()
        .single();

      if (error) {
        throw createError.database(
          'Failed to update document',
          { action: 'update_document', documentId }
        );
      }

      return updatedDocument;
    } catch (error) {
      throw createError.database(
        'Error updating document',
        { action: 'update_document', documentId },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Delete document
  async deleteDocument(documentId: string): Promise<void> {
    try {
      const { error } = await supabase
        .from('documents')
        .delete()
        .eq('id', documentId);

      if (error) {
        throw createError.database(
          'Failed to delete document',
          { action: 'delete_document', documentId }
        );
      }
    } catch (error) {
      throw createError.database(
        'Error deleting document',
        { action: 'delete_document', documentId },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Search documents
  async searchDocuments(query: string, projectId?: string): Promise<Document[]> {
    try {
      let searchQuery = supabase
        .from('documents')
        .select('*')
        .or(`title.ilike.%${query}%,summary.ilike.%${query}%,content.ilike.%${query}%`)
        .order('created_at', { ascending: false });

      if (projectId) {
        searchQuery = searchQuery.eq('project_id', projectId);
      }

      const { data: documents, error } = await searchQuery;

      if (error) {
        throw createError.database(
          'Failed to search documents',
          { action: 'search_documents', query, projectId }
        );
      }

      return documents || [];
    } catch (error) {
      throw createError.database(
        'Error searching documents',
        { action: 'search_documents', query, projectId },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Get document statistics
  async getDocumentStats(projectId?: string): Promise<{
    total: number;
    byType: Record<DocumentType, number>;
    byStatus: Record<string, number>;
    totalSize: number;
  }> {
    try {
      let query = supabase
        .from('documents')
        .select('type, status, file_size');

      if (projectId) {
        query = query.eq('project_id', projectId);
      }

      const { data: documents, error } = await query;

      if (error) {
        throw createError.database(
          'Failed to fetch document statistics',
          { action: 'get_document_stats', projectId }
        );
      }

      const stats = {
        total: documents?.length || 0,
        byType: {} as Record<DocumentType, number>,
        byStatus: {} as Record<string, number>,
        totalSize: 0,
      };

      documents?.forEach(doc => {
        // Count by type
        if (doc.type) {
          stats.byType[doc.type] = (stats.byType[doc.type] || 0) + 1;
        }

        // Count by status
        if (doc.status) {
          stats.byStatus[doc.status] = (stats.byStatus[doc.status] || 0) + 1;
        }

        // Sum file sizes
        if (doc.file_size) {
          stats.totalSize += doc.file_size;
        }
      });

      return stats;
    } catch (error) {
      throw createError.database(
        'Error fetching document statistics',
        { action: 'get_document_stats', projectId },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Update document watch status
  async updateDocumentWatch(documentId: string, watchActive: boolean): Promise<void> {
    try {
      const { error } = await supabase
        .from('documents')
        .update({ watch_active: watchActive })
        .eq('id', documentId);

      if (error) {
        throw createError.database(
          'Failed to update document watch status',
          { action: 'update_document_watch', documentId, watchActive }
        );
      }
    } catch (error) {
      throw createError.database(
        'Error updating document watch status',
        { action: 'update_document_watch', documentId, watchActive },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Get documents needing classification
  async getUnclassifiedDocuments(userId: string, limit: number = 50): Promise<Document[]> {
    try {
      const { data: documents, error } = await supabase
        .from('documents')
        .select('*')
        .eq('created_by', userId) // First filter: documents created by specific user
        .is('project_id', null) // Second filter: only unclassified documents
        .order('created_at', { ascending: false })
        .limit(limit);

      if (error) {
        throw createError.database(
          'Failed to fetch unclassified documents',
          { action: 'get_unclassified_documents' }
        );
      }

      return documents || [];
    } catch (error) {
      throw createError.database(
        'Error fetching unclassified documents',
        { action: 'get_unclassified_documents' },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Assign document to project
  async assignDocumentToProject(documentId: string, projectId: string): Promise<void> {
    try {
      const { error } = await supabase
        .from('documents')
        .update({ project_id: projectId })
        .eq('id', documentId);

      if (error) {
        throw createError.database(
          'Failed to assign document to project',
          { action: 'assign_document_to_project', documentId, projectId }
        );
      }
    } catch (error) {
      throw createError.database(
        'Error assigning document to project',
        { action: 'assign_document_to_project', documentId, projectId },
        error instanceof Error ? error : undefined
      );
    }
  }

  // Get recent documents
  async getRecentDocuments(limit: number = 20, projectId?: string): Promise<Document[]> {
    try {
      let query = supabase
        .from('documents')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(limit);

      if (projectId) {
        query = query.eq('project_id', projectId);
      }

      const { data: documents, error } = await query;

      if (error) {
        throw createError.database(
          'Failed to fetch recent documents',
          { action: 'get_recent_documents', projectId }
        );
      }

      return documents || [];
    } catch (error) {
      throw createError.database(
        'Error fetching recent documents',
        { action: 'get_recent_documents', projectId },
        error instanceof Error ? error : undefined
      );
    }
  }
}

// Export singleton instance
export const documentService = new DocumentService();
export default documentService;
