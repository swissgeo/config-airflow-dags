-- This script is executed with the local postgis docker container
-- The reason being that the image includes this tiger_geocoder extension, which isn't reflected
-- in the database on RDS
-- If we don't drop this, then alembic will pick up on the differences

DO $$
BEGIN
  DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE;
  RAISE NOTICE 'Tiger geocoder extension removed';
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'Tiger geocoder extension not found or already removed';
END $$;


DO $$
BEGIN
  DROP EXTENSION IF EXISTS postgis_topology CASCADE;
  RAISE NOTICE 'Topology extension removed';
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'Topology extension not found or already removed';
END $$;
