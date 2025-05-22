-- Create tables in the correct order based on dependencies
CREATE TABLE IF NOT EXISTS cve (
    cve_id text PRIMARY KEY,
    published_date text,
    last_modified_date text,
    description text,
    nodes text,
    severity text,
    obtain_all_privilege text,
    obtain_user_privilege text,
    obtain_other_privilege text,
    user_interaction_required text,
    cvss2_vector_string text,
    cvss2_access_vector text,
    cvss2_access_complexity text,
    cvss2_authentication text,
    cvss2_confidentiality_impact text,
    cvss2_integrity_impact text,
    cvss2_availability_impact text,
    cvss2_base_score text,
    cvss3_vector_string text,
    cvss3_attack_vector text,
    cvss3_attack_complexity text,
    cvss3_privileges_required text,
    cvss3_user_interaction text,
    cvss3_scope text,
    cvss3_confidentiality_impact text,
    cvss3_integrity_impact text,
    cvss3_availability_impact text,
    cvss3_base_score text,
    cvss3_base_severity text
);

CREATE TABLE IF NOT EXISTS repository (
    repo_url text PRIMARY KEY,
    repo_name text,
    description text,
    homepage text,
    owner text,
    repo_language text,
    stars_count bigint,
    forks_count bigint,
    date_created timestamp without time zone,
    date_last_push timestamp without time zone
);

CREATE TABLE IF NOT EXISTS fixes (
    cve_id text,
    repo_url text,
    hash text,
    rel_type text,
    score bigint,
    extraction_status text,
    PRIMARY KEY (cve_id, repo_url, hash),
    FOREIGN KEY (cve_id) REFERENCES cve(cve_id),
    FOREIGN KEY (repo_url) REFERENCES repository(repo_url)
);

CREATE TABLE IF NOT EXISTS cwe (
    cwe_id text PRIMARY KEY,
    description text
);

CREATE TABLE IF NOT EXISTS cwe_classification (
    cve_id text,
    cwe_id text,
    PRIMARY KEY (cve_id, cwe_id),
    FOREIGN KEY (cve_id) REFERENCES cve(cve_id),
    FOREIGN KEY (cwe_id) REFERENCES cwe(cwe_id)
);
