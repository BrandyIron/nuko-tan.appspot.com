def qsort(src):
    if len(src) < 2:
        return src
    
    pivot = src[0]
    li_rest = src[1:]

    print "[list]" + str(src)
    smaller = []
    for x in li_rest:
        print "[compare] x: " + str(x) + ", pivot: " + str(pivot)
        ans = raw_input()
        
        if ans != str(x):
            smaller.append(x)
        print "[smaller]" + str(smaller)

    larger = []
    for x in li_rest:
        print "[compare] x: " + str(x) + ", pivot: " + str(pivot)
        ans = raw_input()
        
        if ans != str(pivot):
            larger.append(x)
        print "[larger]" + str(larger)
    
    return qsort(smaller) + [pivot] + qsort(larger)

print qsort(['a', 'b', 'c', 'd'])
# print qsort(["tan", "pon", "am"])   