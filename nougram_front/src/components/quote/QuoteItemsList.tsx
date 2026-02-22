import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { QuoteItemInput } from "@/types/quote";
import { Trash2, Plus } from "lucide-react";

interface QuoteItemsListProps {
    items: QuoteItemInput[];
    onChange: (items: QuoteItemInput[]) => void;
}

export function QuoteItemsList({ items, onChange }: QuoteItemsListProps) {

    const addItem = () => {
        onChange([
            ...items,
            {
                service_id: Date.now(), // Temp ID
                pricing_type: "hourly",
                estimated_hours: 0,
                fixed_price: "0",
                quantity: "1",
            },
        ]);
    };

    const removeItem = (index: number) => {
        const newItems = [...items];
        newItems.splice(index, 1);
        onChange(newItems);
    };

    const updateItem = (index: number, field: keyof QuoteItemInput, value: any) => {
        const newItems = [...items];
        newItems[index] = { ...newItems[index], [field]: value };
        onChange(newItems);
    };

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Servicios / Items</CardTitle>
                <Button onClick={addItem} variant="secondary" size="sm" className="gap-2">
                    <Plus className="h-4 w-4" /> Agregar Item
                </Button>
            </CardHeader>
            <CardContent className="space-y-6">
                {items.length === 0 && (
                    <div className="text-center py-8 text-gray-500 border-2 border-dashed rounded-lg">
                        No hay items en la cotización. Agrega uno para comenzar.
                    </div>
                )}

                {items.map((item, index) => (
                    <div key={index} className="p-4 border rounded-lg bg-gray-50 relative animate-in fade-in slide-in-from-top-2">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="absolute top-2 right-2 text-gray-400 hover:text-red-600"
                            onClick={() => removeItem(index)}
                            title="Eliminar item"
                        >
                            <Trash2 className="h-4 w-4" />
                        </Button>

                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 pr-8">
                            {/* Service Selection (Mocked for now) */}
                            <div className="space-y-2">
                                <Label>Servicio</Label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    value={item.pricing_type} // Mocking service name via pricing type selector for UI demo
                                    onChange={(e) => updateItem(index, "pricing_type", e.target.value)}
                                >
                                    <option value="hourly">Por Hora (Hourly)</option>
                                    <option value="fixed">Precio Fijo (Fixed)</option>
                                    <option value="recurring">Recurrente (Monthly)</option>
                                </select>
                            </div>

                            {/* Conditional Fields based on pricing_type */}
                            {item.pricing_type === "hourly" && (
                                <div className="space-y-2">
                                    <Label>Horas Estimadas</Label>
                                    <Input
                                        type="number"
                                        value={item.estimated_hours || 0}
                                        onChange={(e) => updateItem(index, "estimated_hours", parseFloat(e.target.value))}
                                    />
                                </div>
                            )}

                            {(item.pricing_type === "fixed" || item.pricing_type === "recurring") && (
                                <div className="space-y-2">
                                    <Label>{item.pricing_type === "recurring" ? "Precio Mensual" : "Precio Fijo"}</Label>
                                    <Input
                                        isCurrency
                                        value={item.pricing_type === "recurring" ? item.recurring_price : item.fixed_price}
                                        onChange={(e) => updateItem(index, item.pricing_type === "recurring" ? "recurring_price" : "fixed_price", e.target.value)}
                                    />
                                </div>
                            )}

                            {item.pricing_type === "fixed" && (
                                <div className="space-y-2">
                                    <Label>Cantidad</Label>
                                    <Input
                                        type="number"
                                        value={item.quantity || "1"}
                                        onChange={(e) => updateItem(index, "quantity", e.target.value)}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}
