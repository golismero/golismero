class search_results:
	emails = []
	hostnames = []
	people = []

	def extend(self, results):
		self.emails.extend(results.emails)
		self.hostnames.extend(results.hostnames)
		self.people.extend(results.people)

	def remove_duplicates (self):
		self.emails = list(set(self.emails))
		self.hostnames = list(set(self.hostnames))
		self.people = list(set(self.people))