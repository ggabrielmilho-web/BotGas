'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Calendar } from 'lucide-react';
import { format, subDays } from 'date-fns';

interface DateRangeFilterProps {
  onFilterChange: (dateFrom: string | null, dateTo: string | null) => void;
  initialDateFrom?: string;
  initialDateTo?: string;
}

type PresetType = 'today' | 'last7' | 'last30' | 'custom';

export function DateRangeFilter({ onFilterChange, initialDateFrom, initialDateTo }: DateRangeFilterProps) {
  const [selectedPreset, setSelectedPreset] = useState<PresetType>('today');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [showCustom, setShowCustom] = useState(false);

  // Inicializar com data de hoje
  useEffect(() => {
    if (initialDateFrom && initialDateTo) {
      setDateFrom(initialDateFrom);
      setDateTo(initialDateTo);
      setSelectedPreset('custom');
      setShowCustom(true);
    } else {
      applyPreset('today');
    }
  }, []);

  const formatDate = (date: Date): string => {
    return format(date, 'yyyy-MM-dd');
  };

  const applyPreset = (preset: PresetType) => {
    const today = new Date();
    let from: string;
    let to: string = formatDate(today);

    switch (preset) {
      case 'today':
        from = formatDate(today);
        setShowCustom(false);
        break;
      case 'last7':
        from = formatDate(subDays(today, 6)); // 7 dias incluindo hoje
        setShowCustom(false);
        break;
      case 'last30':
        from = formatDate(subDays(today, 29)); // 30 dias incluindo hoje
        setShowCustom(false);
        break;
      case 'custom':
        setShowCustom(true);
        return; // Não aplica automaticamente no modo custom
    }

    setDateFrom(from);
    setDateTo(to);
    setSelectedPreset(preset);
    onFilterChange(from, to);
  };

  const handleCustomApply = () => {
    // Validação: date_from não pode ser maior que date_to
    if (dateFrom && dateTo && dateFrom > dateTo) {
      alert('Data inicial não pode ser maior que data final');
      return;
    }

    if (dateFrom && dateTo) {
      setSelectedPreset('custom');
      onFilterChange(dateFrom, dateTo);
    }
  };

  const handleClear = () => {
    applyPreset('today');
  };

  return (
    <Card className="mb-4">
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Título */}
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <Label className="text-sm font-semibold">Filtro de Período</Label>
          </div>

          {/* Botões de Atalho */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant={selectedPreset === 'today' ? 'default' : 'outline'}
              size="sm"
              onClick={() => applyPreset('today')}
            >
              Hoje
            </Button>
            <Button
              variant={selectedPreset === 'last7' ? 'default' : 'outline'}
              size="sm"
              onClick={() => applyPreset('last7')}
            >
              Últimos 7 dias
            </Button>
            <Button
              variant={selectedPreset === 'last30' ? 'default' : 'outline'}
              size="sm"
              onClick={() => applyPreset('last30')}
            >
              Últimos 30 dias
            </Button>
            <Button
              variant={selectedPreset === 'custom' ? 'default' : 'outline'}
              size="sm"
              onClick={() => applyPreset('custom')}
            >
              Personalizado
            </Button>
          </div>

          {/* Inputs de Data Customizada */}
          {showCustom && (
            <div className="space-y-3 pt-2 border-t">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="date-from" className="text-sm">
                    De:
                  </Label>
                  <Input
                    id="date-from"
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    max={dateTo || undefined}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="date-to" className="text-sm">
                    Até:
                  </Label>
                  <Input
                    id="date-to"
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    min={dateFrom || undefined}
                    max={formatDate(new Date())}
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleCustomApply}
                  disabled={!dateFrom || !dateTo}
                >
                  Aplicar Filtro
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleClear}
                >
                  Limpar
                </Button>
              </div>
            </div>
          )}

          {/* Indicador de período ativo (quando não está em custom) */}
          {!showCustom && dateFrom && dateTo && (
            <div className="text-xs text-muted-foreground">
              Exibindo dados de {format(new Date(dateFrom), 'dd/MM/yyyy')} até {format(new Date(dateTo), 'dd/MM/yyyy')}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
