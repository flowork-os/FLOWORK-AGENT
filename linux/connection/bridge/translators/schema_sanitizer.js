/**
 * ⚡ FLOWORK OS — SCHEMA SANITIZER
 * ================================
 * Component: CONECTION/bridge/translators/schema_sanitizer.js
 * Purpose  : Normalize Gemini uppercase schema types to standard JSON schema lowercase.
 */

function sanitizeSchema(schema) {
    if (!schema || typeof schema !== 'object') return schema;

    if (Array.isArray(schema)) {
        return schema.map(item => sanitizeSchema(item));
    }

    const sanitized = {};
    for (const [key, value] of Object.entries(schema)) {
        if (key === 'type' && typeof value === 'string') {
            sanitized[key] = value.toLowerCase();
        } else if (key === 'properties' && value && typeof value === 'object') {
            sanitized[key] = {};
            for (const [propName, propDef] of Object.entries(value)) {
                sanitized[key][propName] = sanitizeSchema(propDef);
            }
        } else if (key === 'items' && value && typeof value === 'object') {
            sanitized[key] = sanitizeSchema(value);
        } else if (typeof value === 'object' && value !== null) {
            sanitized[key] = sanitizeSchema(value);
        } else {
            sanitized[key] = value;
        }
    }

    return sanitized;
}

module.exports = {
    sanitizeSchema
};
