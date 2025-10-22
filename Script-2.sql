
drop table 
-- типы договоров
CREATE TABLE contract_types (
    type_id         serial PRIMARY KEY,
    type_name       text NOT NULL UNIQUE
);
--стадии исполнения
CREATE TABLE stages (
    stage_id        serial PRIMARY KEY,
    stage_name      text NOT NULL UNIQUE
);

-- ставки НДС
CREATE TABLE vat_rates (
    vat_id          serial PRIMARY KEY,
    vat_percent     numeric(5,2) NOT NULL CHECK (vat_percent >= 0 AND vat_percent <= 100)
);

-- организации
CREATE TABLE organizations (
    org_id          bigserial PRIMARY KEY,
    name            text NOT NULL,
    postal_index    varchar(20),
    address         text,
    phone           varchar(50),
    fax             varchar(50),
    inn             varchar(20) UNIQUE,
    corr_account    varchar(50),
    bank            text,
    settlement_account varchar(50),
    okonh           varchar(20),
    okpo            varchar(20),
    bik             varchar(20),
    created_at      timestamptz DEFAULT now()
);

-- виды оплат
CREATE TABLE payment_types (
    payment_type_id serial PRIMARY KEY,
    payment_type_name text NOT NULL UNIQUE
);

-- договора
CREATE TABLE contracts (
    contract_id         bigserial PRIMARY KEY,
    contract_code       text NOT NULL UNIQUE, -- _код договора_
    contract_date       date NOT NULL DEFAULT current_date,
    customer_org_id     bigint NOT NULL REFERENCES organizations(org_id),
    contractor_org_id   bigint NOT NULL REFERENCES organizations(org_id),
    type_id             int NOT NULL REFERENCES contract_types(type_id),
    stage_id            int NOT NULL REFERENCES stages(stage_id),
    vat_id              int REFERENCES vat_rates(vat_id),
    exec_date           date, -- дата исполнения
    subject             text, -- тема
    note                text,
    total_sum        	numeric(14,2) NOT NULL CHECK (total_sum >= 0) DEFAULT 0.00,
    total_paid          numeric(14,2) NOT NULL DEFAULT 0.00 CHECK (total_paid >= 0), 
    created_at          timestamptz DEFAULT now()
);

-- этапы договора
CREATE TABLE contract_stages (
    contract_id     bigint NOT NULL REFERENCES contracts(contract_id) ON DELETE CASCADE,
    stage_no        integer NOT NULL CHECK (stage_no > 0),
    planned_exec_date date,
    stage_id  int NOT NULL REFERENCES stages(stage_id) ON DELETE RESTRICT,
    stage_sum       numeric(14,2) NOT NULL CHECK (stage_sum >= 0),
    advance_sum     numeric(14,2) DEFAULT 0.00 CHECK (advance_sum >= 0),
    topic           text,
    PRIMARY KEY (contract_id, stage_no)
);

-- оплата
CREATE TABLE payments (
    payment_id      bigserial PRIMARY KEY,
    contract_id     bigint NOT NULL REFERENCES contracts(contract_id) ON DELETE CASCADE,
    payment_date    date NOT NULL DEFAULT current_date,
    payment_sum     numeric(14,2) NOT NULL CHECK (payment_sum >= 0),
    payment_type_id smallint REFERENCES payment_types(payment_type_id),
    payment_doc_no  text,
    note            text,
    created_at      timestamptz DEFAULT now()
);

--  Индексы (для ускорения поиска и фильтров)
CREATE INDEX idx_contracts_customer ON contracts(customer_org_id);
CREATE INDEX idx_contracts_contractor ON contracts(contractor_org_id);
CREATE INDEX idx_contracts_date ON contracts(contract_date);
CREATE INDEX idx_payments_contract ON payments(contract_id);
CREATE INDEX idx_contract_stages_contract ON contract_stages(contract_id);


-- триггер 1
-- Функция пересчёта total_paid
CREATE OR REPLACE FUNCTION trg_recalc_contract_total_paid() RETURNS trigger
AS $$
BEGIN
    -- пересчитать total_paid для связанного контракта
    UPDATE contracts
    SET total_paid = COALESCE((
            SELECT SUM(payment_sum) FROM payments WHERE contract_id = COALESCE(NEW.contract_id, OLD.contract_id)
        ), 0.00)
    WHERE contract_id = COALESCE(NEW.contract_id, OLD.contract_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER payments_after_insert
AFTER INSERT OR UPDATE OR DELETE ON payments
FOR EACH ROW
EXECUTE FUNCTION trg_recalc_contract_total_paid();


--тригер 2
CREATE OR REPLACE FUNCTION trg_recalc_contract_total_sum()
RETURNS trigger
AS $$
BEGIN
    UPDATE contracts
    SET total_sum = COALESCE((
            SELECT SUM(stage_sum) 
            FROM contract_stages 
            WHERE contract_id = COALESCE(NEW.contract_id, OLD.contract_id)
        ), 0.00)
    WHERE contract_id = COALESCE(NEW.contract_id, OLD.contract_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER recalc_contract_total_sum
AFTER INSERT OR UPDATE OR DELETE ON contract_stages
FOR EACH ROW
EXECUTE FUNCTION trg_recalc_contract_total_sum();

-- view 1
-- 1) VIEW по одной таблице: краткая карточка организации
CREATE VIEW v_orgs_short AS
SELECT org_id, name, postal_index, address, phone, inn
FROM organizations;

-- view 2 дебиторская задолженность
CREATE OR REPLACE VIEW view_contracts_balance AS
SELECT
    contracts.contract_code,
    contracts.contract_date,
    customer_org.name AS customer_name,
    contractor_org.name AS contractor_name,
    contracts.total_sum,
    contracts.total_paid,
    (contracts.total_sum - contracts.total_paid) AS debt_amount
FROM contracts
JOIN organizations AS customer_org ON contracts.customer_org_id = customer_org.org_id
JOIN organizations AS contractor_org ON contracts.contractor_org_id = contractor_org.org_id
WHERE (contracts.total_sum - contracts.total_paid) > 0
ORDER BY debt_amount DESC;

-- view 3 сколько всего договоров и на какую сумму
CREATE OR REPLACE VIEW view_customer_contract_stats AS
SELECT
    customer_org.name AS customer_name,
    COUNT(contracts.contract_id) AS total_contracts,
    SUM(contracts.total_sum) AS total_contract_sum
FROM contracts
JOIN organizations AS customer_org ON contracts.customer_org_id = customer_org.org_id
GROUP BY customer_org.name
HAVING SUM(contracts.total_sum) > 1000000
ORDER BY total_contract_sum DESC;



--
CREATE OR REPLACE VIEW view_contracts_simple AS
SELECT
    contracts.contract_id,
    contracts.contract_code,
    contracts.contract_date,
    customer_org.name AS customer_name,
    contractor_org.name AS contractor_name,
    contracts.total_sum
FROM contracts
JOIN organizations AS customer_org ON contracts.customer_org_id = customer_org.org_id
JOIN organizations AS contractor_org ON contracts.contractor_org_id = contractor_org.org_id
ORDER BY contracts.contract_date DESC;--