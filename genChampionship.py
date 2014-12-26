from argparse import ArgumentParser
from sys import exit
from csv import reader

from random import choice

VENUE_FIELD = 0
TRACK_FIELD = 1
LAPLEN_FIELD = 2
LAPS_FIELD = 3
CUSTLAPS_FIELD = 4
NOTE_FIELD = 5

class Track:
	def __init__(self, venue, name, laplength, laps, note):
		self.venue = venue
		self.name = name
		self.laplength = laplength
		self.laps = laps
		self.note = note
		self.speedway = False

class Venue:
	def __init__(self, name):
		self.name = name
		self.tracks = {}
		self.selected = []
		
	def pickTrack(self):
		if not self.tracks: return None
		return self.tracks.pop(choice(self.tracks.keys()))
		
class Pool:
	def __init__(self, n):
		self.venues = {}
		self.selvenues = {}
		self.selected = []
		self.speedways = 0
		self.ntracks = n
		self.ttracks = 0
		self.maxpvenue = 2
		
	def load(self, fname):
		with open(fname, "rb") as csvfile:
			csvreader = reader(csvfile)
			rowcount = 0
			prevven = None
			currven = None
			for row in csvreader:
				rowcount += 1
				if rowcount < 2: continue
				venue = row[VENUE_FIELD]
				track = row[TRACK_FIELD]
				if not venue and not track:
					continue
				if venue and venue != prevven:
					currven = Venue(venue)
					self.venues[venue] = currven
				if track:
					if row[CUSTLAPS_FIELD]:
						t = Track(currven.name, track, row[LAPLEN_FIELD], row[CUSTLAPS_FIELD], row[NOTE_FIELD])
					else:
						t = Track(currven.name, track, row[LAPLEN_FIELD], row[LAPS_FIELD], row[NOTE_FIELD])
					currven.tracks[track] = t
					self.ttracks += 1
				
		
	def selections(self, ls):
		for selection in ls.split(","):
			try:
				venue, trackname = selection.split("-")
				self.doselection(self.venues[venue], trackname)
			except (ValueError, KeyError):
				print "Skipping (%s), invalid." % selection
				continue
	
	def doselection(self, venue, trackname=None):
		if trackname:
			if trackname not in venue.tracks: raise KeyError
			# increment venue counter
			if venue.name not in self.selvenues: self.selvenues[venue.name] = 1
			else: self.selvenues[venue.name] += 1
			
			t = venue.tracks.pop(trackname)
			if t.speedway: self.speedways += 1
			self.selected.append(t)
			if not venue.tracks: self.venues.pop(venue.name) # remove empty venues from pool
		else:
			raise ValueError
	
	def pickVenue(self):
		vs = self.venues.keys()
		vn = choice(vs)
		if self.maxpvenue == 0: return self.venues[vn]
		while self.selvenues.get(vn, 0) >= 2:
			vn = choice(vs)
		return self.venues[vn]
		
	
	def generate(self):
		while self.ntracks > 0:
			v = self.pickVenue()
			t = v.pickTrack()
			if not v.tracks: self.venues.pop(v.name) # remove empty venues from pool
			while t is None or ((self.speedways > 2) and t.speedway):
				v = self.pickVenue()
				t = v.pickTrack()
				if not v.tracks: self.venues.pop(v.name) # remove empty venues from pool
			# increment venue counter
			if v.name not in self.selvenues: self.selvenues[v.name] = 1
			else: self.selvenues[v.name] += 1
			if t.speedway: self.speedways += 1
			self.selected.append(t)
			self.ntracks -=1
		
	def printall(self):
		for venue in self.venues.itervalues():
			for track in venue.tracks.itervalues():
				print venue.name, track.name, track.laplength, track.laps
	
	def printselected(self):
		print "Venue-Trackname, Lapsize, Laps, notes"
		for track in self.selected:
			print "%s-%s, %s, %s, %s" % (track.venue, track.name, track.laplength, track.laps, track.note)
			
	def _countreducedtracks(self):
		count = 0
		for v in self.venues.values():
			vc = 0
			for t in v.tracks:
				if vc >= 2: break
				vc += 1
				count += 1
		return count
		
if __name__ == '__main__':
	parser = ArgumentParser(description="FORZA CHAMPIONSHIP GENERATOR", 
		epilog="Gunna need a file to load track pool from. csv please.")
	parser.add_argument("-s", "--load-selections", dest="selections", 
		metavar="SELECTIONS", help="Comma separated list of Venue-Trackname.")
	parser.add_argument("-n", "--num-tracks", type=int, dest="numtracks", 
		metavar="NUMTRACKS", default=10, help="Number of tracks to generate. Default 10.")

	parser.add_argument('tracklist', nargs="?", metavar="TRACKLIST.csv", default=None,
		help="filename of tracklist to load. Must be CSV. First 2 lines are ignored.")
	
	args = parser.parse_args()
	
	if not args.tracklist:
		print "Require tracklist"
		exit(1)
	
	p = Pool(args.numtracks)
	p.load(args.tracklist)
	
	if p.ttracks < p.ntracks:
		print "Error: don't have %d tracks available." % p.ntracks
		exit(1)
	
	if p.ntracks > p._countreducedtracks(): p.maxpvenue = 0
	
	if args.selections:
		p.selections(args.selections)
	
	p.generate()
	
	p.printselected()