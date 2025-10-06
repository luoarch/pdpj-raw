'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Search, X } from 'lucide-react';
import { Button } from '@/components/atoms/button';
import { Input } from '@/components/atoms/input';
import { Card, CardContent } from '@/components/atoms/card';

const searchSchema = z.object({
  query: z.string().min(1, 'Digite o número do processo'),
});

type SearchFormData = z.infer<typeof searchSchema>;

interface SearchFormProps {
  onSearch: (data: SearchFormData) => void;
  loading?: boolean;
  showAdvanced?: boolean;
}

export function SearchForm({ onSearch, loading = false, showAdvanced = false }: SearchFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SearchFormData>({
    resolver: zodResolver(searchSchema),
  });

  const onSubmit = (data: SearchFormData) => {
    onSearch(data);
  };

  const handleClear = () => {
    reset();
    onSearch({ query: '' });
  };

  return (
    <Card>
      <CardContent className="p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Campo de busca principal */}
          <div className="flex gap-2">
            <div className="flex-1">
              <div>
                <Input
                  {...register('query')}
                  placeholder="Ex: 1000145-91.2023.8.26.0597"
                />
                {errors.query && (
                  <p className="text-red-500 text-sm mt-1">{errors.query.message}</p>
                )}
              </div>
            </div>
            <Button type="submit" loading={loading}>
              <Search className="h-4 w-4 mr-2" />
              Consultar
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={handleClear}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
