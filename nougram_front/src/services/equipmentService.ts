
import { Equipment, DepreciationResult } from '@/types/equipment';
import { calculateDepreciation } from '@/lib/depreciation';

// Mock Data Storage
let EQUIPMENT_STORAGE: Equipment[] = [
    {
        id: '1',
        name: 'MacBook Pro 16 M2',
        category: 'Hardware',
        purchasePrice: 12000000,
        purchaseDate: '2024-01-15',
        currency: 'COP',
        usefulLifeMonths: 36,
        salvageValue: 2000000,
        depreciationMethod: 'straight_line',
        isActive: true,
        createdAt: '2024-01-15T10:00:00Z'
    },
    {
        id: '2',
        name: 'Cámara Canon EOS R5',
        category: 'Hardware',
        purchasePrice: 8500000,
        purchaseDate: '2023-06-10',
        currency: 'COP',
        usefulLifeMonths: 36,
        salvageValue: 1500000,
        depreciationMethod: 'straight_line',
        isActive: true,
        createdAt: '2023-06-10T10:00:00Z'
    }
];

export const equipmentService = {
    getAll: async (): Promise<Equipment[]> => {
        return new Promise((resolve) => {
            setTimeout(() => resolve([...EQUIPMENT_STORAGE]), 300);
        });
    },

    getById: async (id: string): Promise<Equipment | undefined> => {
        return new Promise((resolve) => {
            setTimeout(() => resolve(EQUIPMENT_STORAGE.find(e => e.id === id)), 200);
        });
    },

    create: async (equipment: Omit<Equipment, 'id' | 'createdAt'>): Promise<Equipment> => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const newEquipment: Equipment = {
                    ...equipment,
                    id: Math.random().toString(36).substring(7),
                    createdAt: new Date().toISOString()
                };
                EQUIPMENT_STORAGE.unshift(newEquipment);
                resolve(newEquipment);
            }, 500);
        });
    },

    update: async (id: string, updates: Partial<Equipment>): Promise<Equipment> => {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                const index = EQUIPMENT_STORAGE.findIndex(e => e.id === id);
                if (index === -1) {
                    reject(new Error('Equipment not found'));
                    return;
                }
                EQUIPMENT_STORAGE[index] = { ...EQUIPMENT_STORAGE[index], ...updates };
                resolve(EQUIPMENT_STORAGE[index]);
            }, 500);
        });
    },

    delete: async (id: string): Promise<void> => {
        return new Promise((resolve) => {
            setTimeout(() => {
                EQUIPMENT_STORAGE = EQUIPMENT_STORAGE.filter(e => e.id !== id);
                resolve();
            }, 500);
        });
    },

    // Business Logic: Generate Schedule
    getDepreciationSchedule: (equipment: Equipment, monthsToShow?: number) => {
        // We can reuse logic from `calculateDepreciation` but iterate month by month
        // For now, let's implement a generator compliant with Requirements Section 4.1
        const schedule = [];
        const limit = monthsToShow || equipment.usefulLifeMonths + 1; // +1 to ensure we see the end

        // Mock implementation for schedule - in real app, this would duplicate logic from `lib` or `lib` would support iteration
        // Let's use `lib/depreciation` logic by simulating "now" moving forward
        // Note: This is computationally expensive if loop is large, but for < 120 iterations it's fine.

        const purchaseDate = new Date(equipment.purchaseDate);

        for (let i = 1; i <= limit; i++) {
            // Calculate date for month i
            const date = new Date(purchaseDate);
            date.setMonth(date.getMonth() + i);

            // Create a temp equipment object "as if" it was purchased i months ago vs "now" being date
            // Actually `calculateDepreciation` takes (equipment) and compares to `new Date()`.
            // We can't easily mock `new Date()` inside `lib` without dependency injection.
            // REFRACTOR: We should probably move the `now` param to `calculateDepreciation`?
            // Since `lib/depreciation.ts` is existing, let's check if we can modify it or logic duplication.
            // Logic duplication for schedule is often cleaner than complex "time travel" logic in core calculator.

            // Simple Straight Line logic for schedule (most common)
            if (equipment.depreciationMethod === 'straight_line') {
                // ... logic ...
            }
        }

        return []; // To be implemented fully in step 2
    },

    // Quick helper exposed
    calculateCurrentStats: (equipment: Equipment): DepreciationResult => {
        return calculateDepreciation(equipment);
    }
};
