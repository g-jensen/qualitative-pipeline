export const DEFAULT_DOCUMENT_ID = "001"

export function quote(class_: any, text: any, documentId?: string) {
  documentId = documentId || DEFAULT_DOCUMENT_ID
  return {class: class_, text: text, documentId: documentId};
}