
export interface ExecutiveSummaryRequest {
    projectName: string;
    clientName: string;
    clientSector?: string;
    services: {
        name: string;
        price: number;
    }[];
    totalPrice: number;
    currency: string;
    language?: 'es' | 'en';
}

export interface ExecutiveSummaryResponse {
    summary: string;
    provider: string; // 'OpenAI' | 'Anthropic' | etc.
}

export const aiService = {
    generateExecutiveSummary: async (data: ExecutiveSummaryRequest): Promise<ExecutiveSummaryResponse> => {
        // Simulate API delay
        return new Promise((resolve) => {
            setTimeout(() => {
                const summary = `
**Resumen Ejecutivo: ${data.projectName}**

Preparado para: ${data.clientName} ${data.clientSector ? `(${data.clientSector})` : ''}

Esta propuesta detalla la implementación de los servicios solicitados con un enfoque en calidad y eficiencia. El alcance incluye:

${data.services.map(s => `- **${s.name}**: ${data.currency} ${s.price.toLocaleString()}`).join('\n')}

**Inversión Total Estimada:** ${data.currency} ${data.totalPrice.toLocaleString()}

Nuestro equipo se compromete a entregar resultados medibles que impulsen los objetivos estratégicos de ${data.clientName}.
                `.trim();

                resolve({
                    summary,
                    provider: 'MockAI'
                });
            }, 1500); // Simulate AI processing time
        });
    }
};
