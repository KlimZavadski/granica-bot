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

### 002_rename_passport_checkpoints.sql

**Дата:** 2024-11-29
**Описание:** Переименовывает чекпоинты паспортного контроля с "invited" на "passed" для более точного отражения момента записи времени

**Изменения:**
- `invited_passport_control_1` → `passed_passport_control_1`
- `invited_passport_control_2` → `passed_passport_control_2`

**Обратная совместимость:** ✅ Да (код поддерживает оба названия)

---

### 003_remove_leaving_checkpoint_1.sql

**Дата:** 2024-11-30
**Описание:** Убирает промежуточный чекпоинт `leaving_checkpoint_1` из обязательных, упрощая процесс отслеживания

**Изменения:**
- `leaving_checkpoint_1` помечен как optional (не обязательный)
- Сокращение с 7 до 6 обязательных чекпоинтов

**Обратная совместимость:** ✅ Да (старые данные остаются валидными)

---

### dev_clear_test_data.sql

**Дата:** 2024-11-30
**Описание:** ⚠️ **ТОЛЬКО ДЛЯ РАЗРАБОТКИ** - Очищает все данные о поездках и событиях

**⚠️ ВНИМАНИЕ:** Это удалит ВСЕ записи из таблиц `journeys` и `journey_events`!

**Использование:**
```bash
# Во время разработки для очистки тестовых данных
./scripts/run_migration.sh dev_clear_test_data.sql
```

**Изменения:**
- Удаляет все записи из `journey_events`
- Удаляет все записи из `journeys`
- Выводит количество удаленных записей для проверки

**Применение:** ⚠️ Только в dev окружении! Никогда не использовать в production!

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

