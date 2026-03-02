
import { apiRequest } from '@/lib/api-client';

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

type BackendExecutiveSummaryResponse = {
    summary: string;
    provider: string;
};

export const aiService = {
    generateExecutiveSummary: async (data: ExecutiveSummaryRequest): Promise<ExecutiveSummaryResponse> => {
        const payload = {
            project_name: data.projectName,
            client_name: data.clientName,
            client_sector: data.clientSector,
            services: data.services.map((service, index) => ({
                service_id: index + 1,
                service_name: service.name,
                client_price: service.price,
            })),
            total_price: data.totalPrice,
            currency: data.currency,
            language: data.language || 'es',
        };

        const response = await apiRequest<BackendExecutiveSummaryResponse>('/ai/generate-executive-summary', {
            method: 'POST',
            body: JSON.stringify(payload),
        });

        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudo generar el resumen ejecutivo con el backend');
        }

        return {
            summary: response.data.summary,
            provider: response.data.provider,
        };
    }
};
