import axios from "axios";

export const translateText = async (text, targetLang) => {
    if (!text) return "";

    // 🔹 Partimos el texto en trozos de 500 caracteres
    const chunks = [];
    for (let i = 0; i < text.length; i += 500) {
        chunks.push(text.substring(i, i + 500));
    }

    const translatedChunks = [];

    for (const chunk of chunks) {
        try {
            const response = await axios.get("https://api.mymemory.translated.net/get", {
                params: {
                    q: chunk,
                    langpair: `en|${targetLang}`
                }
            });

            const translated = response.data.responseData.translatedText;
            translatedChunks.push(translated);

            // guardamos en cache localStorage
            localStorage.setItem(
                `translation_${targetLang}_${btoa(chunk)}`,
                translated
            );
        } catch (error) {
            console.error("Error al traducir:", error);
            translatedChunks.push(chunk); // fallback al original
        }
    }

    // 🔹 Unimos todos los trozos traducidos
    return translatedChunks.join(" ");
};
