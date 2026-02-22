
export interface Template {
    id: string;
    name: string;
    amount: number;
    currency: string;
}

// Mock templates available in the system
const AVAILABLE_TEMPLATES: Template[] = [
    { id: 'laptop', name: 'Laptop de Trabajo', amount: 800000, currency: 'COP' },
    { id: 'monitor', name: 'Monitor Externo', amount: 150000, currency: 'COP' },
    { id: 'adobe', name: 'Adobe CC', amount: 150000, currency: 'COP' },
    { id: 'chatgpt', name: 'ChatGPT Plus', amount: 20, currency: 'USD' },
    { id: 'hosting', name: 'Hosting Web', amount: 50000, currency: 'COP' },
    { id: 'internet', name: 'Internet', amount: 80000, currency: 'COP' },
    { id: 'coworking', name: 'Coworking', amount: 300000, currency: 'COP' },
    { id: 'notion', name: 'Notion Pro', amount: 8, currency: 'USD' },
    { id: 'autocad', name: 'AutoCAD', amount: 150, currency: 'USD' },
    { id: 'revit', name: 'Revit', amount: 200, currency: 'USD' },
    { id: 'sketchup', name: 'SketchUp', amount: 100, currency: 'USD' },
];

export const templateService = {
    getAll: async (): Promise<Template[]> => {
        // Simulate API call
        return new Promise((resolve) => {
            setTimeout(() => resolve([...AVAILABLE_TEMPLATES]), 100);
        });
    },

    search: async (query: string): Promise<Template[]> => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const lowerQuery = query.toLowerCase();
                const results = AVAILABLE_TEMPLATES.filter(t =>
                    t.name.toLowerCase().includes(lowerQuery)
                );
                resolve(results);
            }, 100);
        });
    }
};
