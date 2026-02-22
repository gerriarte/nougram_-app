
export interface Client {
    id: string;
    name: string;
    email?: string;
    sector?: string;
    projectCount: number;
}

// Mock clients for now
const MOCK_CLIENTS: Client[] = [
    { id: '1', name: 'TechCorp', email: 'contact@techcorp.com', sector: 'Technology', projectCount: 3 },
    { id: '2', name: 'StartupX', email: 'hello@startupx.io', sector: 'SaaS', projectCount: 1 },
    { id: '3', name: 'DesignCo', email: 'info@designco.agency', sector: 'Design', projectCount: 5 },
    { id: '4', name: 'MarketFit', email: 'growth@marketfit.com', sector: 'Marketing', projectCount: 2 },
    { id: '5', name: 'OldSchool', email: 'admin@oldschool.edu', sector: 'Education', projectCount: 10 },
    { id: '6', name: 'HealthPlus', email: 'info@healthplus.org', sector: 'Healthcare', projectCount: 0 },
];

export const clientService = {
    searchClients: async (query: string): Promise<Client[]> => {
        // Simulate API delay
        return new Promise((resolve) => {
            setTimeout(() => {
                if (!query) {
                    resolve([]);
                    return;
                }

                const lowerQuery = query.toLowerCase();
                const filtered = MOCK_CLIENTS.filter(client =>
                    client.name.toLowerCase().includes(lowerQuery) ||
                    client.email?.toLowerCase().includes(lowerQuery)
                );

                resolve(filtered);
            }, 300);
        });
    }
};
