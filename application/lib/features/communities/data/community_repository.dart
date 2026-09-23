import 'dart:async';

class Community {
  const Community({
    required this.id,
    required this.name,
    required this.description,
    required this.members,
    required this.activeUsers,
    required this.distance,
    required this.image,
    required this.tags,
    required this.joined,
    required this.posts,
    required this.announcement,
    required this.membersList,
  });

  final String id;
  final String name;
  final String description;
  final int members;
  final int activeUsers;
  final String distance;
  final String image;
  final List<String> tags;
  final bool joined;
  final List<CommunityPost> posts;
  final String announcement;
  final List<CommunityMember> membersList;
}

class CommunityPost {
  const CommunityPost({
    required this.id,
    required this.author,
    required this.authorInitials,
    required this.time,
    required this.title,
    required this.body,
    required this.likes,
    required this.commentCount,
    required this.liked,
    this.image,
  });

  final String id;
  final String author;
  final String authorInitials;
  final String time;
  final String title;
  final String body;
  final int likes;
  final int commentCount;
  final bool liked;
  final String? image;
}

class CommunityMember {
  const CommunityMember({required this.name, required this.initials, required this.role, required this.active});

  final String name;
  final String initials;
  final String role;
  final bool active;
}

class CommunityComment {
  const CommunityComment({required this.author, required this.initials, required this.text, required this.time, required this.likes, required this.liked});

  final String author;
  final String initials;
  final String text;
  final String time;
  final int likes;
  final bool liked;
}

abstract interface class CommunityRepository {
  Future<List<Community>> getNearbyCommunities();

  Future<Community> getCommunity(String id);

  Future<CommunityPost> getPost(String communityId, String postId);

  Future<List<CommunityComment>> getComments(String communityId, String postId);
}

class MockCommunityRepository implements CommunityRepository {
  const MockCommunityRepository();

  static final _communities = <Community>[
    Community(
      id: 'islamabad',
      name: 'Islamabad Community',
      description: 'A trusted local network helping neighbours return lost items, pets, and documents.',
      members: 12700,
      activeUsers: 1300,
      distance: '2.4 km away',
      image: 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80',
      tags: ['Islamabad', 'LostAndFound', 'Neighbourhood'],
      joined: true,
      announcement: 'Please share verified sightings and avoid posting personal addresses publicly. Meet in a public place when possible.',
      membersList: [
        CommunityMember(name: 'Ayesha Malik', initials: 'AM', role: 'Admin', active: true),
        CommunityMember(name: 'Mustafa Khan', initials: 'MK', role: 'Moderator', active: true),
        CommunityMember(name: 'Hira Shah', initials: 'HS', role: 'Member', active: false),
      ],
      posts: [
        CommunityPost(id: 'wallet', author: 'Mustafa Khan', authorInitials: 'MK', time: '2h ago', title: 'Found a wallet near Centaurus Mall', body: 'Brown leather wallet found near the west entrance. I have it safe and can verify the contents privately.', likes: 32, commentCount: 8, liked: false, image: 'https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=900&q=80'),
        CommunityPost(id: 'cat', author: 'Hira Shah', authorInitials: 'HS', time: '5h ago', title: 'Missing black cat around Bani Gala', body: 'Small black cat with a red collar. Please message here if you have seen her nearby.', likes: 18, commentCount: 4, liked: true, image: 'https://images.unsplash.com/photo-1518791841217-8f162f1e1131?auto=format&fit=crop&w=900&q=80'),
      ],
    ),
    Community(
      id: 'f10',
      name: 'F-10 Sector',
      description: 'Fast local alerts for lost and found reports around F-10 and nearby sectors.',
      members: 850,
      activeUsers: 98,
      distance: '4.1 km away',
      image: 'https://images.unsplash.com/photo-1493246507139-91e8fad9978e?auto=format&fit=crop&w=1200&q=80',
      tags: ['F10', 'LocalAlerts', 'QuickResponse'],
      joined: false,
      announcement: 'Keep posts concise and include the nearest landmark for faster community response.',
      membersList: [
        CommunityMember(name: 'Sara Ahmed', initials: 'SA', role: 'Admin', active: true),
        CommunityMember(name: 'Bilal Raza', initials: 'BR', role: 'Member', active: true),
      ],
      posts: [
        CommunityPost(id: 'keys', author: 'Sara Ahmed', authorInitials: 'SA', time: '1h ago', title: 'Keys found outside the market', body: 'A small keyring was found near the main entrance this afternoon.', likes: 9, commentCount: 2, liked: false),
      ],
    ),
    Community(
      id: 'students',
      name: 'University Students',
      description: 'Students helping students recover essentials across Islamabad campuses.',
      members: 950,
      activeUsers: 110,
      distance: '6.8 km away',
      image: 'https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1200&q=80',
      tags: ['Students', 'Campus', 'StudyLife'],
      joined: false,
      announcement: 'Use your university building and floor as the location, never a private room or dorm address.',
      membersList: [
        CommunityMember(name: 'Zain Abbas', initials: 'ZA', role: 'Admin', active: true),
        CommunityMember(name: 'Mariam Noor', initials: 'MN', role: 'Member', active: false),
      ],
      posts: [],
    ),
  ];

  @override
  Future<List<Community>> getNearbyCommunities() async {
    await Future<void>.delayed(const Duration(milliseconds: 550));
    return List.unmodifiable(_communities);
  }

  @override
  Future<Community> getCommunity(String id) async {
    await Future<void>.delayed(const Duration(milliseconds: 450));
    return _communities.firstWhere((community) => community.id == id, orElse: () => _communities.first);
  }

  @override
  Future<CommunityPost> getPost(String communityId, String postId) async {
    final community = await getCommunity(communityId);
    return community.posts.firstWhere((post) => post.id == postId, orElse: () => community.posts.first);
  }

  @override
  Future<List<CommunityComment>> getComments(String communityId, String postId) async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    return const [
      CommunityComment(author: 'Hira Shah', initials: 'HS', text: 'I think this may be mine. I can verify the initials privately.', time: '10m ago', likes: 6, liked: false),
      CommunityComment(author: 'Ayesha Malik', initials: 'AM', text: 'I can help verify the wallet details when you meet.', time: '8m ago', likes: 3, liked: true),
    ];
  }
}
