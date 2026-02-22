
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Alert, AlertDescription } from '../ui/Alert';

interface StepIdentityProps {
    onNext: (data: any) => void;
    initialData?: any;
}

export function StepIdentity({ onNext, initialData }: StepIdentityProps) {
    const [organizationName, setOrganizationName] = useState(initialData?.organizationName || '');
    const [currency, setCurrency] = useState(initialData?.currency || '');
    const [country, setCountry] = useState(initialData?.country || '');
    const [errors, setErrors] = useState<any>({});

    const validate = () => {
        const newErrors: any = {};
        if (!organizationName.trim()) newErrors.organizationName = 'El nombre de la organización es requerido';
        if (!currency) newErrors.currency = 'La moneda es requerida';
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = () => {
        if (validate()) {
            onNext({ organizationName, currency, country });
        }
    };

    return (
        <div className="space-y-6 max-w-2xl mx-auto">
            <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold text-gray-900">¡Bienvenido a Nougram!</h1>
                <p className="text-gray-600">Vamos a configurar tu estructura de costos en menos de 10 minutos.</p>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 flex items-start gap-3">
                <span className="text-xl">🔒</span>
                <p className="text-sm text-gray-600">
                    <strong>Tus datos financieros están cifrados</strong> y solo se usan para calcular tus márgenes personales. Nadie más los verá.
                </p>
            </div>

            <Card>
                <CardContent className="space-y-4 pt-6">
                    <div className="space-y-2">
                        <Label htmlFor="orgName">Nombre de tu Organización *</Label>
                        <Input
                            id="orgName"
                            placeholder="Ej: Mi Agencia Creativa"
                            value={organizationName}
                            onChange={(e) => setOrganizationName(e.target.value)}
                            className={errors.organizationName ? 'border-red-500' : ''}
                        />
                        {errors.organizationName && <p className="text-red-500 text-sm">{errors.organizationName}</p>}
                        <p className="text-xs text-gray-500">ℹ️ Este nombre aparecerá en tus cotizaciones.</p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="currency">Moneda Primaria *</Label>
                        <select
                            id="currency"
                            className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${errors.currency ? 'border-red-500' : ''}`}
                            value={currency}
                            onChange={(e) => setCurrency(e.target.value)}
                        >
                            <option value="">Seleccionar moneda...</option>
                            <option value="COP">COP - Peso Colombiano</option>
                            <option value="USD">USD - Dólar Estadounidense</option>
                            <option value="ARS">ARS - Peso Argentino</option>
                            <option value="EUR">EUR - Euro</option>
                        </select>
                        {errors.currency && <p className="text-red-500 text-sm">{errors.currency}</p>}
                        <p className="text-xs text-gray-500">ℹ️ Todos los cálculos se harán en esta moneda.</p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="country">País</Label>
                        <select
                            id="country"
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                            value={country}
                            onChange={(e) => setCountry(e.target.value)}
                        >
                            <option value="">Seleccionar país...</option>
                            <option value="COL">Colombia</option>
                            <option value="USA">Estados Unidos</option>
                            <option value="ARG">Argentina</option>
                            <option value="MEX">México</option>
                        </select>
                        <p className="text-xs text-gray-500">ℹ️ Esto nos ayuda a sugerirte impuestos y cargas sociales correctas.</p>
                    </div>
                </CardContent>
            </Card>

            <div className="flex justify-end">
                <Button onClick={handleNext} className="w-full sm:w-auto">
                    Siguiente →
                </Button>
            </div>
        </div>
    );
}
