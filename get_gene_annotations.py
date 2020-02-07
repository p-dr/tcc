# description: Removes non-gene annotations from S. mansoni genome annotations. Calculates gene length.
# in: pardir/'genome_annotation/sm_annotations.gff3'
# out: pardir/'genome_annotation/gene_annotations.gff3'

from pandas import read_csv
from utils import pardir, redo_flag, GFF3_COLUMNS, unfold_gff
from wget import download
from subprocess import call
import os

#raw_annotations_path = pardir/'genome_annotation/schistosoma_mansoni.PRJEA36577.WBPS12.annotations'
annotations_path = pardir/'genome_annotation/gene_annotations.gff3'
annotations_url = ('ftp://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS13/species/schistosoma_mansoni/PRJEA36577/schistosoma_mansoni.PRJEA36577.WBPS13.annotations.gff3.gz')
raw_annotations_path = pardir/'genome_annotation'/annotations_url.split('/')[-1]

if not raw_annotations_path.with_suffix('').exists() or redo_flag:
    print('Downloading gff...')
    download(annotations_url, str(raw_annotations_path))
    print(f'\nDownloaded {raw_annotations_path}. Unzipping...')
    call(f'gunzip "{raw_annotations_path}"', shell=True)
    

#============== REMOVER ANOTAÇÕES NÃO-GÊNICAS ===============#

print(f"Lendo '{str(raw_annotations_path).strip('.gz')}'...")
raw_annotations = read_csv(raw_annotations_path.with_suffix(''),
                           sep='\t', comment='#',
                           header=None, names=GFF3_COLUMNS)


print('Leitura encerrada. Removendo anotações não-gênicas...')

genes_gff = raw_annotations.loc[raw_annotations['type'] == 'gene']
genes_gff[['start', 'end']].astype(int, inplace=True)

lengths = genes_gff.end - genes_gff.start
genes_gff.loc[:, 'attributes'] = genes_gff.attributes.str.replace('ID=gene:', 'gene_id=')
genes_gff['attributes'] = genes_gff.attributes.str.extract(r'(gene_id.*Name[^;]+)')
# com loc não funciona (?!):
# genes_gff.loc[:, 'attributes'] = genes_gff.attributes.str.extract(r'(gene_id.*Name[^;]+)')
genes_gff.loc[:, 'attributes'] += ';length=' + lengths.astype(str)


# ###### REMOVER GENES COM FIM OU INÍCIO COINCIDENTES
genes_gff = genes_gff.loc[lengths.sort_values().index]  # Ordenar por tamanho
# Manter o maior gene entre os que coincidem.
genes_gff = genes_gff.drop_duplicates(['seqid', 'start'], keep='last')
genes_gff = genes_gff.drop_duplicates(['seqid', 'end'], keep='last')

if genes_gff.duplicated(['seqid', 'start']).sum() or genes_gff.duplicated(['seqid', 'end']).sum():
    print('HÁ GENES COM INÍCIO/TÉRMINO DUPLICADOS:')
    print(genes_gff[genes_gff.duplicated(['seqid', 'start'], keep=False)])
    print(genes_gff[genes_gff.duplicated(['seqid', 'end'], keep=False)])
    raise ValueError

genes_gff = genes_gff.sort_values(['seqid', 'start'])
genes_gff.to_csv(annotations_path, sep='\t', index=False, header=None)

print(f"Anotações gênicas mantidas em '{str(annotations_path)}'.")
