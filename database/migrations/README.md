# Database Migrations

## Как применить миграции

### Через Supabase Dashboard (Рекомендуется)

1. Открой [Supabase Dashboard](https://app.supabase.com)
2. Выбери свой проект
3. Перейди в **SQL Editor**
4. Скопируй содержимое файла миграции (например `001_add_cancelled_field.sql`)
5. Вставь в редактор
6. Нажми **Run**

### Через psql

```bash
psql "YOUR_CONNECTION_STRING" -f database/migrations/001_add_cancelled_field.sql
```

---

## Список миграций

### 001_add_cancelled_field.sql

**Дата:** 2024-11-29
**Описание:** Добавляет поле `cancelled` в таблицу `journeys` для различения отменённых и завершённых поездок

**Изменения:**
- Добавлено поле `cancelled BOOLEAN DEFAULT false`
- Добавлен индекс для запросов завершённых не отменённых поездок

**Обратная совместимость:** ✅ Да (graceful fallback в коде)

---

## Проверка применения миграции

```sql
-- Проверить что поле добавлено
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'journeys' AND column_name = 'cancelled';

-- Должно вернуть:
-- cancelled | boolean | YES | false
```

---

## Rollback (откат)

Если нужно откатить миграцию:

```sql
-- 001_add_cancelled_field.sql rollback
DROP INDEX IF EXISTS idx_journeys_completed_not_cancelled;
ALTER TABLE journeys DROP COLUMN IF EXISTS cancelled;
```

---

## Примечания

- Все миграции **опциональны** - код работает и без них
- Бот имеет fallback механизмы для обратной совместимости
- Применяй миграции только если нужна расширенная функциональность
- Всегда делай backup перед применением миграций в production

