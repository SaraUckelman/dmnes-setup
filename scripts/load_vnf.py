#!/usr/bin/python3 -b

import sys

from dmnes import *


def x_for_y(dbh, table, xcol, ycol, yval):
  dbh.execute(
    "SELECT {} FROM {} WHERE {} = ?".format(xcol, table, ycol),
    (yval,)
  )
  row = dbh.fetchone()
  return row[0] if row else None


def id_for_nym(dbh, nym):
  return x_for_y(dbh, 'cnf', 'id', 'nym', nym)


def id_for_bib_key(dbh, key):
  return x_for_y(dbh, 'bib', 'id', 'key', key)


def area_for_place(vnf):
# TODO: handle # country != 1
  if hasattr(vnf, 'place'):
    if hasattr(vnf.place, 'country'):
      return str(vnf.place.country)
    elif hasattr(vnf.place, 'region'):
      return str(vnf.place.region)
  return 'Unspecified'


def make_vnf_row(dbh, vnf, spanned_vnf):
  return (
    str(vnf.name),
    str(vnf.gen),
    str(vnf.case),
    int(vnf.dim),
    str(vnf.lang),
    area_for_place(vnf),
    str_inner(spanned_vnf.place) if hasattr(vnf, 'place') else None,
    str(vnf.date),
    id_for_bib_key(dbh, str(vnf.bibl.key)),
    str(spanned_vnf.bibl.loc) if hasattr(vnf.bibl, 'loc') else None
  )


def insert_vnf(dbh, vnf, spanned_vnf):
  vnf_r = make_vnf_row(dbh, vnf, spanned_vnf)
  dbh.execute(
    "INSERT INTO vnf (name, gen, 'case', dim, lang, area, place, date, bib_id, bib_loc) VALUES (?,?,?,?,?,?,?,?,?,?)",
    vnf_r
  )
  return dbh.lastrowid


def make_vnf_nyms_rows(dbh, vnf_id, vnf):
  return tuple((vnf_id, id_for_nym(dbh, str(nym))) for nym in vnf.nym)


def insert_vnf_nyms(dbh, vnf_id, vnf):
  if hasattr(vnf, 'nym'):
    vnf_nyms_rs = make_vnf_nyms_rows(dbh, vnf_id, vnf)
    dbh.executemany(
      "INSERT INTO vnf_cnf (vnf, cnf) VALUES (?,?)",
      vnf_nyms_rs
    )


def process_vnf(parser, trans, dbh, filename):
  vnf = parse_xml(parser, filename)
  spanned_vnf = trans(vnf).getroot()
  vnf_id = insert_vnf(dbh, vnf, spanned_vnf)
  insert_vnf_nyms(dbh, vnf_id, vnf)
  insert_notes(dbh, "vnf_notes", vnf_id, spanned_vnf)


def main():
  parser = make_validating_parser(sys.argv[2])
  trans = make_xslt(sys.argv[3])
  xml_to_db(parser, trans, process_vnf, sys.argv[1], sys.argv[4:])


if __name__ == '__main__':
  main()
