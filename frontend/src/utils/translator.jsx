import axios from "axios";

export const translateText = async (text, targetLang) => {
    if (!text) return "";


    if (typeof text !== 'string' || text.trim().length === 0) {
        return "";
    }


    const chunks = [];
    const chunkSize = 500;
    
    for (let i = 0; i < text.length; i += chunkSize) {
        chunks.push(text.substring(i, i + chunkSize));
    }

    const translatedChunks = [];

    for (const chunk of chunks) {
        try {

            const cacheKey = `translation_${targetLang}_${btoa(chunk)}`;
            const cached = localStorage.getItem(cacheKey);
            
            if (cached) {
                translatedChunks.push(cached);
                continue;
            }


            const response = await axios.get("https://api.mymemory.translated.net/get", {
                params: {
                    q: chunk,
                    langpair: `en|${targetLang}`,

                },
                timeout: 10000 
            });

            if (response.data && response.data.responseData) {
                const translated = response.data.responseData.translatedText;
                translatedChunks.push(translated);
                

                try {
                    localStorage.setItem(cacheKey, translated);
                } catch (storageError) {
                    console.warn("No se pudo guardar en caché:", storageError);
                }
            } else {

                translatedChunks.push(chunk);
            }

        } catch (error) {
            console.error("Error al traducir chunk:", error);
            translatedChunks.push(chunk); 
        }
    }

 
    return translatedChunks.join(" ");
};


export const clearTranslationCache = () => {
    Object.keys(localStorage)
        .filter(key => key.startsWith('translation_'))
        .forEach(key => localStorage.removeItem(key));
};