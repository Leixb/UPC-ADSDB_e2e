SELECT table_name
  FROM information_schema.tables
 WHERE table_schema='formatted'
   AND table_type='BASE TABLE';