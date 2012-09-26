# import unittest
# import pprint


# class TestRelatedCitation(unittest.TestCase):

#     maxDiff = None

#     def test_parse_all(self):
#         for string, data in samples:
#             _data = parse(Lexer, Parser, ParserState, string)
#             import pdb;pdb.set_trace()
#             # pprint.pprint(data)
#             # pprint.pprint(_data)
#             #self.assertEqual(data, _data)

def main():
    from gpolocator import schemes

    import pdb;pdb.set_trace()
    schemes.Token('ll').get_schemes()

    for k, v in schemes._schemes_lists.items():
        print v
        for t in v:
            en = schemes.Enum(t)
            print en
            try:
                print en.get_schemes()
                print en.get_ordinality()
            except Exception as e:
                print 'got', e
                import pdb;pdb.set_trace()
                en.get_ordinality()
            # print en.get_schemes()



if __name__ == '__main__':
    main()
