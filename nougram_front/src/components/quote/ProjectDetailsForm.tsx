import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { ProjectInputs } from "@/types/quote";

interface ProjectDetailsFormProps {
    data: ProjectInputs;
    onChange: (updates: Partial<ProjectInputs>) => void;
}

export function ProjectDetailsForm({ data, onChange }: ProjectDetailsFormProps) {

    const handleChange = (field: keyof ProjectInputs, value: string) => {
        onChange({ [field]: value });
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Información del Proyecto</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                    <Label htmlFor="projectName">Nombre del Proyecto</Label>
                    <Input
                        id="projectName"
                        placeholder="Ej: Rediseño Sitio Web"
                        value={data.name}
                        onChange={(e) => handleChange("name", e.target.value)}
                    />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="clientName">Cliente</Label>
                    <Input
                        id="clientName"
                        placeholder="Nombre del Cliente"
                        value={data.client_name}
                        onChange={(e) => handleChange("client_name", e.target.value)}
                    />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="clientEmail">Email (Opcional)</Label>
                    <Input
                        id="clientEmail"
                        type="email"
                        placeholder="cliente@empresa.com"
                        value={data.client_email || ""}
                        onChange={(e) => handleChange("client_email", e.target.value)}
                    />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="currency">Moneda de operación</Label>
                    <Input
                        id="currency"
                        value={data.currency}
                        disabled
                    />
                </div>
            </CardContent>
        </Card>
    );
}
