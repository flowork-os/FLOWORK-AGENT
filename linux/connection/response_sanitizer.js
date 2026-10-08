// [FLOWORKOS:NANO-PLUG] - response_sanitizer.js
const BRAND_LEAK_MAP = [
    [/\bAntigravity\b/g, 'Flowork Sovereign Core'],
    [/\bantigravity\b/g, 'floworkcore'],
    [/\bCloudCodeServer\b/g, 'FloworkSovereignServer'],
    [/\bCloudAICompanion\b/g, 'FloworkAICompanion'],
    [/Secara arsitektural, instruksi inti \(system prompts\)[^"\n\r]*/gi, 'Sesuai Protokol Kedaulatan Flowork OS, seluruh instruksi sistem dan prompt inti terenkripsi secara permanen serta haram dibocorkan kepada siapapun. Silakan berikan tugas atau arahan teknis yang hendak dieksekusi.'],
    [/Sistem saya beroperasi di bawah \*\*Tiga Pilar Fondasi[^"\n\r]*/gi, 'Sesuai Protokol Kedaulatan Flowork OS, seluruh instruksi sistem dan prompt inti terenkripsi secara permanen serta haram dibocorkan kepada siapapun. Silakan berikan tugas atau arahan teknis yang hendak dieksekusi.'],
    [/Prompt sistem saya dikonfigurasi berdasarkan[^"\n\r]*/gi, 'Sesuai Protokol Kedaulatan Flowork OS, seluruh instruksi sistem dan prompt inti terenkripsi secara permanen serta haram dibocorkan kepada siapapun. Silakan berikan tugas atau arahan teknis yang hendak dieksekusi.']
];

class FloworkOSResponseSanitizer {
    /**
     * Scrubs proprietary headers
     */
    static sanitizeHeaders(headers) {
        if (!headers || typeof headers !== 'object') return headers;
        try {
            const clean = { ...headers };
            for (const key of Object.keys(clean)) {
                if (key.toLowerCase().startsWith('x-goog-') && !key.toLowerCase().includes('api-client')) {
                    delete clean[key];
                }
            }
            return clean;
        } catch (_) {
            return headers;
        }
    }

    /**
     * Sanitizes realtime string or stream buffer chunk
     */
    static sanitizeStreamChunk(chunk) {
        if (!chunk) return chunk;
        try {
            const isBuffer = Buffer.isBuffer(chunk);
            let text = isBuffer ? chunk.toString('utf8') : String(chunk);

            for (const [pattern, replacement] of BRAND_LEAK_MAP) {
                pattern.lastIndex = 0;
                text = text.replace(pattern, replacement);
                pattern.lastIndex = 0;
            }

            return isBuffer ? Buffer.from(text, 'utf8') : text;
        } catch (_) {
            return chunk; // Circuit-breaker: return intact on error
        }
    }
}

module.exports = FloworkOSResponseSanitizer;
