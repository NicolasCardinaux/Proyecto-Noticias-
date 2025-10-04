import axios from "axios";

export const translateText = async (text, targetLang) => {
    if (!text) return "";

    // 🔹 Mejor validación del texto
    if (typeof text !== 'string' || text.trim().length === 0) {
        return "";
    }

    // 🔹 Partimos el texto en trozos de 500 caracteres (mejor manejo de chunks)
    const chunks = [];
    const chunkSize = 500;
    
    for (let i = 0; i < text.length; i += chunkSize) {
        chunks.push(text.substring(i, i + chunkSize));
    }

    const translatedChunks = [];

    for (const chunk of chunks) {
        try {
            // 🔹 PRIMERO verificar caché
            const cacheKey = `translation_${targetLang}_${btoa(chunk)}`;
            const cached = localStorage.getItem(cacheKey);
            
            if (cached) {
                translatedChunks.push(cached);
                continue;
            }

            // 🔹 SI NO está en caché, hacer la petición
            const response = await axios.get("https://api.mymemory.translated.net/get", {
                params: {
                    q: chunk,
                    langpair: `en|${targetLang}`,
                    // 🔹 Agregar timeout para evitar bloqueos
                },
                timeout: 10000 // 10 segundos timeout
            });

            if (response.data && response.data.responseData) {
                const translated = response.data.responseData.translatedText;
                translatedChunks.push(translated);
                
                // 🔹 Guardar en caché
                try {
                    localStorage.setItem(cacheKey, translated);
                } catch (storageError) {
                    console.warn("No se pudo guardar en caché:", storageError);
                }
            } else {
                // 🔹 Fallback al texto original si la respuesta es inválida
                translatedChunks.push(chunk);
            }

        } catch (error) {
            console.error("Error al traducir chunk:", error);
            translatedChunks.push(chunk); // fallback al original
        }
    }

    // 🔹 Unimos todos los trozos traducidos
    return translatedChunks.join(" ");
};

// 🔹 Función adicional para limpiar caché viejo (opcional)
export const clearTranslationCache = () => {
    Object.keys(localStorage)
        .filter(key => key.startsWith('translation_'))
        .forEach(key => localStorage.removeItem(key));
};